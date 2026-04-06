# CLI Reference

All commands accept `-v` / `--verbose` for debug logging.

## `s3-folder-sync init`

Initialize sync configuration for a directory. Creates a `.s3sync/` folder containing `config.toml` and sets up the storage connection.

```bash
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://s3.amazonaws.com \
  --bucket my-sync-bucket \
  --region us-east-1 \
  --access-key "YOUR_ACCESS_KEY" \
  --secret-key "YOUR_SECRET_KEY" \
  --machine-id mac-1 \
  --backend s3
```

| Flag | Description |
|------|-------------|
| `--path` | Directory to sync (default: current directory) |
| `--endpoint` | Storage endpoint URL |
| `--bucket` | Bucket or storage zone name |
| `--prefix` | Optional key prefix within the bucket |
| `--region` | Storage region (default: `us-east-1`) |
| `--access-key` | Access key / API key |
| `--secret-key` | Secret key / API password |
| `--machine-id` | Unique identifier for this machine (default: hostname) |
| `--backend` | Storage backend: `s3` or `bunny` (default: `s3`) |

## `s3-folder-sync start`

Start the sync daemon. Watches the folder for changes and syncs every 10 seconds (configurable).

```bash
# Foreground (logs to terminal, Ctrl+C to stop)
s3-folder-sync start --path ~/Workspace

# Background (detaches from terminal, writes to .s3sync/daemon.log)
s3-folder-sync start --path ~/Workspace -d
```

| Flag | Description |
|------|-------------|
| `--path` | Synced directory |
| `-d` | Run as background daemon |

### Foreground vs background

- **Foreground** (`start`) — the process runs in your terminal. You see logs in real time. Press `Ctrl+C` to stop. Use this when testing or debugging.
- **Background** (`start -d`) — the process detaches from the terminal and runs silently. Logs go to `.s3sync/daemon.log`. The process survives closing the terminal. Use `s3-folder-sync stop` to shut it down. Use this for day-to-day operation.

Both modes do exactly the same syncing. The only difference is where the process runs and where logs go.

## `s3-folder-sync stop`

Stop a running background daemon.

```bash
s3-folder-sync stop --path ~/Workspace
```

Has no effect on foreground processes (use `Ctrl+C` for those).

## `s3-folder-sync status`

Show current sync status: machine ID, bucket, whether the daemon is running, and how many files are tracked.

```bash
s3-folder-sync status --path ~/Workspace
```

Example output:

```
Watch path: /Users/you/Workspace
Machine ID: mac-1
Bucket: my-sync-bucket
Daemon: running (PID 12345)
Tracked files: 42 synced, 0 pending delete
```

## `s3-folder-sync sync`

Force a single sync cycle immediately, then exit. Useful for one-off syncs or cron jobs.

```bash
s3-folder-sync sync --path ~/Workspace
```

## `s3-folder-sync conflicts`

List or clean conflict files. Conflict files are created when the same file is edited on two machines before either syncs. The remote version becomes the canonical file, and the local version is saved as `<name>.conflict.<machine-id>.<timestamp>.<ext>`.

```bash
# List conflict files
s3-folder-sync conflicts --path ~/Workspace

# Delete all conflict files
s3-folder-sync conflicts --clean --path ~/Workspace
```

Conflict files are local-only — they are never synced to remote storage.

## `s3-folder-sync menubar`

Launch a macOS menu bar app showing sync status. Requires the `menubar` extra (`pip install -e ".[menubar]"`).

```bash
s3-folder-sync menubar --path ~/Workspace
```
