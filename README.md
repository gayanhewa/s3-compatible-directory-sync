# s3-compatible-directory-sync

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
- **Soft deletes** — deleted files go to a local trash folder with a configurable grace period
- **Multiple backends** — S3-compatible storage (AWS S3, Cloudflare R2, MinIO, Backblaze B2) and Bunny.net Edge Storage
- **Background daemon** — runs as a background process, syncs every 10 seconds by default
- **Menu bar app** — optional macOS menu bar icon for at-a-glance status
- **Ignore patterns** — skip `.git/`, `node_modules/`, `.DS_Store`, etc.

## Install

```bash
git clone https://github.com/gayanhewa/s3-compatible-directory-sync.git
cd s3-compatible-directory-sync
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Optional: menu bar support
pip install -e ".[menubar]"
```

Or with pipx:

```bash
pipx install git+https://github.com/gayanhewa/s3-compatible-directory-sync.git
```

Requires Python 3.11+.

## Quick Start

```bash
# 1. Initialize
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://s3.amazonaws.com \
  --bucket my-sync-bucket \
  --access-key "YOUR_KEY" \
  --secret-key "YOUR_SECRET" \
  --machine-id mac-1

# 2. Start syncing (foreground, Ctrl+C to stop)
s3-folder-sync start --path ~/Workspace

# 3. Or run in background
s3-folder-sync start --path ~/Workspace -d
```

### Setting up a second machine

```bash
s3-folder-sync init --path ~/Workspace ...  # same bucket, different --machine-id
s3-folder-sync sync --path ~/Workspace      # pull all existing files first
s3-folder-sync start --path ~/Workspace -d  # then start the daemon
```

> **Important:** Always run `sync` before `start` on a new machine. If the folder already contains files (e.g. a partial copy), skipping this step may cause spurious conflicts.

### Other commands

```bash
s3-folder-sync status --path ~/Workspace              # check daemon and file count
s3-folder-sync sync --path ~/Workspace                 # force one-off sync cycle
s3-folder-sync conflicts --path ~/Workspace            # list conflict files
s3-folder-sync conflicts --clean --path ~/Workspace    # delete all conflict files
s3-folder-sync stop --path ~/Workspace                 # stop background daemon
s3-folder-sync menubar --path ~/Workspace              # macOS menu bar app
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLI Reference](docs/cli-reference.md) | Every command, flag, and option explained |
| [How Sync Works](docs/how-sync-works.md) | Sync algorithm, conflict resolution, soft deletes, configuration |
| [Local Testing Guide](docs/local-testing.md) | Test bidirectional sync on one machine with two folders |
| [Bunny.net Setup](docs/bunny-net-setup.md) | Step-by-step guide for Bunny.net Edge Storage, including launchd auto-start |

## Development

```bash
git clone https://github.com/gayanhewa/s3-compatible-directory-sync.git
cd s3-compatible-directory-sync
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
