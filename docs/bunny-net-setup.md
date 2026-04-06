# Setting Up with Bunny.net

Bunny.net offers Edge Storage with a native REST API. This tool has a built-in Bunny backend (`--backend bunny`) that works with it directly.

## 1. Create a Storage Zone

1. Log in to [bunny.net dashboard](https://dash.bunny.net)
2. Go to **Storage** > **Add Storage Zone**
3. Name it (e.g. `workspace-sync`)
4. Select your **primary region** (pick the one closest to you)

## 2. Get Your Credentials

1. Go to **Storage** > select your zone > **FTP & API Access**
2. Note the **Password** — this is your access key
3. Note the **Hostname** — this is your endpoint

| Region | Endpoint |
|--------|----------|
| Falkenstein (EU) | `storage.bunnycdn.com` |
| New York (US) | `ny.storage.bunnycdn.com` |
| Los Angeles (US) | `la.storage.bunnycdn.com` |
| Singapore (SG) | `sg.storage.bunnycdn.com` |
| Sydney (AU) | `syd.storage.bunnycdn.com` |
| London (UK) | `uk.storage.bunnycdn.com` |

## 3. Initialize and start

```bash
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://syd.storage.bunnycdn.com \
  --bucket your-zone-name \
  --access-key "your-storage-password" \
  --secret-key "your-storage-password" \
  --machine-id mac-1 \
  --backend bunny

# Test with a foreground run first
s3-folder-sync start --path ~/Workspace

# Once confirmed working, run in background
s3-folder-sync start --path ~/Workspace -d
```

## 4. Set up the second machine

Same steps, different `--machine-id`:

```bash
s3-folder-sync init \
  --path ~/Workspace \
  --endpoint https://syd.storage.bunnycdn.com \
  --bucket your-zone-name \
  --access-key "your-storage-password" \
  --secret-key "your-storage-password" \
  --machine-id mac-2 \
  --backend bunny

# Pull existing files, then start daemon
s3-folder-sync sync --path ~/Workspace
s3-folder-sync start --path ~/Workspace -d
```

## 5. Run on login (macOS)

Create a Launch Agent to start automatically:

```bash
cat > ~/Library/LaunchAgents/com.s3foldersync.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.s3foldersync</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which s3-folder-sync)</string>
        <string>start</string>
        <string>--path</string>
        <string>$HOME/Workspace</string>
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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No config found" | Run `s3-folder-sync init` in the target directory first |
| Auth errors | Verify your storage zone password in the Bunny dashboard |
| Files not syncing | Check `s3-folder-sync status`, run with `-v` for debug logs |
| Conflict files appearing | Both machines edited the same file. Review `.conflict.*` files, keep what you want, then `conflicts --clean` |
| Daemon won't start | Check if one is already running: `s3-folder-sync status` |
