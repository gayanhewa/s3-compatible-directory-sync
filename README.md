# s3-folder-sync

Sync a local folder to S3-compatible object storage across multiple machines. Designed for keeping Obsidian vaults, notes, dotfiles, or any file-based workspace in sync without a third-party sync service.

```
┌─────────┐       ┌─────────────┐       ┌─────────┐
│  Mac 1  │──────▶│  S3 Bucket  │◀──────│  Mac 2  │
│ (watch) │◀──────│  (source of │──────▶│ (watch) │
└─────────┘       │   truth)    │       └─────────┘
                  └─────────────┘
```

## Features

- **Real-time sync** — watches for file changes with debounce for rapid saves (Obsidian-friendly)
- **Conflict resolution** — both sides edited? Remote wins as canonical, local saved as `.conflict.*` file. No data is ever lost.
- **Soft deletes** — deleted files go to a local trash folder with a grace period before propagating
- **S3-compatible** — works with AWS S3, Bunny.net, Cloudflare R2, MinIO, Backblaze B2, etc.
- **Background daemon** — runs as a background process, syncs every 10 seconds by default
- **Ignore patterns** — skip `.git/`, `node_modules/`, `.DS_Store`, etc.

## Install

```bash
# From source
pip install -e .

# Or with pipx (recommended, isolated environment)
pipx install git+https://github.com/gayanhewa/s3-folder-sync.git
```

Requires Python 3.11+.

## Quick Start

```bash
# Initialize sync for a directory
s3-folder-sync init --path ~/Workspace \
  --endpoint https://s3.amazonaws.com \
  --bucket my-sync-bucket \
  --machine-id mac-1

# Start syncing (foreground)
s3-folder-sync start --path ~/Workspace

# Start syncing (background daemon)
s3-folder-sync start --path ~/Workspace -d

# Check status
s3-folder-sync status --path ~/Workspace

# Force a one-shot sync
s3-folder-sync sync --path ~/Workspace

# List conflict files
s3-folder-sync conflicts --path ~/Workspace

# Stop background daemon
s3-folder-sync stop --path ~/Workspace
```

## CLI Reference

| Command      | Description                          |
|-------------|--------------------------------------|
| `init`      | Initialize config in `.s3sync/`      |
| `start`     | Start sync daemon (`-d` for background) |
| `stop`      | Stop background daemon               |
| `status`    | Show sync status and tracked files   |
| `sync`      | Force immediate sync cycle           |
| `conflicts` | List unresolved conflict files       |

Global flags: `-v` / `--verbose` for debug logging.

## How Sync Works

1. **Scan local** — detect new, modified, and deleted files
2. **List remote** — query S3 for current objects
3. **Diff** — compare local state, remote state, and last-known-synced state (SQLite)
4. **Resolve**:
   - Changed locally only → push to S3
   - Changed remotely only → pull from S3
   - Changed on both sides → **conflict**: remote wins, local saved as `file.conflict.<machine>.<timestamp>.ext`
   - Deleted locally → schedule remote delete (with grace period)
   - Deleted remotely → move local to `.s3sync/trash/`
5. **Edit always wins over delete** — if one machine edits and another deletes, the edit is preserved

## Configuration

Stored in `<watch-path>/.s3sync/config.toml`:

```toml
[storage]
endpoint = "https://storage.bunnycdn.com"
bucket = "my-zone"
prefix = "workspace/"
region = "us-east-1"
access_key = ""
secret_key = ""

[sync]
interval = 10          # seconds between sync cycles
debounce = 2.0         # seconds to wait after file change
delete_grace_period = 300  # seconds before propagating deletes

[machine]
id = "mac-1"           # unique per machine

[ignore]
patterns = [
  ".DS_Store",
  "*.tmp",
  ".git/**",
  "node_modules/**",
  ".s3sync/**",
]
```

---

## Runbook: Setting Up with Bunny.net

Bunny.net offers Edge Storage with an S3-compatible API (currently in preview). Here's how to set it up.

### 1. Create a Storage Zone

1. Log in to [bunny.net dashboard](https://dash.bunny.net)
2. Go to **Storage** → **Add Storage Zone**
3. Name it (e.g. `workspace-sync`)
4. Select your **primary region** (pick the one closest to you)
5. Optionally enable replication regions for redundancy

### 2. Get Your Credentials

1. Go to **Storage** → select your zone → **FTP & API Access**
2. Note the **Password** — this is your storage API key
3. Note the **Hostname** — this is your endpoint (e.g. `storage.bunnycdn.com`)

The endpoint varies by region:
| Region | Endpoint |
|--------|----------|
| Falkenstein (EU) | `storage.bunnycdn.com` |
| New York (US) | `ny.storage.bunnycdn.com` |
| Los Angeles (US) | `la.storage.bunnycdn.com` |
| Singapore (SG) | `sg.storage.bunnycdn.com` |
| Sydney (AU) | `syd.storage.bunnycdn.com` |
| London (UK) | `uk.storage.bunnycdn.com` |

> **Note:** Bunny.net's S3-compatible API is in closed preview as of early 2026. If S3 compatibility isn't available on your zone yet, check [their blog](https://bunny.net/blog/) for updates on GA availability. In the meantime, you can use any other S3-compatible provider (AWS S3, Cloudflare R2, MinIO, Backblaze B2).

### 3. Initialize on Machine 1

```bash
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://storage.bunnycdn.com \
  --bucket my-zone-name \
  --prefix "workspace/" \
  --access-key "your-storage-password" \
  --secret-key "your-storage-password" \
  --machine-id mac-1
```

### 4. Start the Daemon on Machine 1

```bash
# Test with a foreground run first
s3-folder-sync start --path ~/Workspace

# Once confirmed working, run in background
s3-folder-sync start --path ~/Workspace -d
```

### 5. Set Up Machine 2

Repeat the init with a **different machine-id**:

```bash
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://storage.bunnycdn.com \
  --bucket my-zone-name \
  --prefix "workspace/" \
  --access-key "your-storage-password" \
  --secret-key "your-storage-password" \
  --machine-id mac-2

s3-folder-sync start --path ~/Workspace -d
```

### 6. Verify Sync

```bash
# On Mac 1
echo "hello from mac 1" > ~/Workspace/test-sync.md

# Wait ~10 seconds, then on Mac 2
cat ~/Workspace/test-sync.md
# Should show: hello from mac 1
```

### 7. Run on Login (macOS)

Create a Launch Agent to start the daemon automatically:

```bash
cat > ~/Library/LaunchAgents/com.s3foldersync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.s3foldersync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/s3-folder-sync</string>
        <string>start</string>
        <string>--path</string>
        <string>/Users/you/Workspace</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/s3-folder-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/s3-folder-sync.err</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.s3foldersync.plist
```

Replace `/path/to/s3-folder-sync` with the actual path (find it with `which s3-folder-sync`).

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "No config found" | Run `s3-folder-sync init` in the target directory first |
| Auth errors | Verify your storage zone password in the Bunny dashboard |
| Files not syncing | Check `s3-folder-sync status`, run with `-v` for debug logs |
| Conflict files appearing | Both machines edited the same file — review `.conflict.*` files and keep the version you want |
| Daemon won't start | Check if one is already running: `s3-folder-sync status` |

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
