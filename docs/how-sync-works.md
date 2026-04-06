# How Sync Works

## Sync Cycle

Each sync cycle runs these steps:

1. **Scan local** — walk the directory, hash every file, compare against last-known state in SQLite
2. **List remote** — query storage for current objects and their metadata
3. **Diff** — compare local state, remote state, and last-synced state to determine what changed
4. **Resolve and execute** — apply the appropriate action for each file

## Resolution Table

| Scenario | Action |
|----------|--------|
| New local file | Push to remote |
| New remote file | Pull to local |
| Local edit only | Push to remote |
| Remote edit only | Pull to local |
| Both edited (same content) | No-op |
| Both edited (different content) | **Conflict** — pull remote as canonical, save local as `.conflict.*` |
| Deleted locally | Schedule remote delete (after grace period) |
| Deleted remotely | Move local to `.s3sync/trash/<date>/` |
| One side edited, other deleted | Edit wins (safer) |

## Conflict Resolution

When the same file is modified on two machines between sync cycles:

1. The **remote version wins** and becomes the canonical file
2. The **local version is saved** as `<name>.conflict.<machine-id>.<timestamp>.<ext>`
3. Conflict files are **local-only** — they are never pushed to remote storage
4. Review conflict files manually, keep what you want, then run `s3-folder-sync conflicts --clean`

## Soft Deletes

When a file is deleted locally:

1. The delete is **not propagated immediately** — it's scheduled with a configurable grace period (default: 5 minutes)
2. This prevents accidental data loss from rapid delete propagation between machines
3. The grace period is configured via `sync.delete_grace_period` in `config.toml`

When a file is deleted remotely:

1. The local copy is **moved to `.s3sync/trash/<date>/`** rather than being permanently deleted
2. You can recover accidentally deleted files from the trash directory

## State Tracking

Sync state is tracked in a local SQLite database at `.s3sync/state.db`. For each file it stores:

- Relative path
- Content hash (SHA-256)
- Local modification time
- Last synced ETag (or content hash for Bunny backend)
- Last synced timestamp

This allows the engine to determine whether a file changed locally, remotely, or both since the last sync.

## Configuration

Stored in `<watch-path>/.s3sync/config.toml`:

```toml
[storage]
endpoint = "https://syd.storage.bunnycdn.com"
bucket = "my-zone"
prefix = ""
region = "syd"
access_key = "your-key"
secret_key = "your-key"
backend = "bunny"   # "s3" or "bunny"

[sync]
interval = 10          # seconds between sync cycles
debounce = 2.0         # seconds to wait after file change before syncing
delete_grace_period = 300  # seconds before propagating deletes to remote

[machine]
id = "mac-1"           # unique per machine, used in conflict filenames

[ignore]
patterns = [
  ".DS_Store",
  "*.tmp",
  ".git/**",
  "node_modules/**",
  ".s3sync/**",
  "*.conflict.*",
]
```
