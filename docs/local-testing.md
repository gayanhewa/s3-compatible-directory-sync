# Local Testing Guide

You can verify bidirectional sync on a single machine by using two separate folders that act as two "machines".

## 1. Set up storage

Use any S3-compatible service, or for fully local testing, run [MinIO](https://min.io/):

```bash
# Option A: Use an existing bucket (AWS, Bunny, R2, etc.)
# Option B: Run MinIO locally
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# Create a bucket via the MinIO console at http://localhost:9001
# or with: aws --endpoint-url http://localhost:9000 s3 mb s3://test-sync
```

## 2. Create two folders

```bash
mkdir -p ~/test-sync/machine-1
mkdir -p ~/test-sync/machine-2
```

## 3. Initialize both with the same bucket, different machine IDs

```bash
# Machine 1
s3-folder-sync init \
  --path ~/test-sync/machine-1 \
  --endpoint http://localhost:9000 \
  --bucket test-sync \
  --access-key minioadmin \
  --secret-key minioadmin \
  --machine-id machine-1 \
  --backend s3

# Machine 2
s3-folder-sync init \
  --path ~/test-sync/machine-2 \
  --endpoint http://localhost:9000 \
  --bucket test-sync \
  --access-key minioadmin \
  --secret-key minioadmin \
  --machine-id machine-2 \
  --backend s3
```

## 4. Start both daemons (use two terminals)

```bash
# Terminal 1
s3-folder-sync start --path ~/test-sync/machine-1

# Terminal 2
s3-folder-sync start --path ~/test-sync/machine-2
```

## 5. Test sync

```bash
# Create a file on machine-1
echo "hello from machine 1" > ~/test-sync/machine-1/test.md

# Wait ~10 seconds, then check machine-2
cat ~/test-sync/machine-2/test.md
# Output: hello from machine 1

# Edit on machine-2
echo "edited on machine 2" >> ~/test-sync/machine-2/test.md

# Wait ~10 seconds, then check machine-1
cat ~/test-sync/machine-1/test.md
# Output: hello from machine 1
#         edited on machine 2
```

## 6. Test conflict resolution

```bash
# Stop both daemons (Ctrl+C in each terminal)

# Edit the same file on both sides
echo "version A" > ~/test-sync/machine-1/test.md
echo "version B" > ~/test-sync/machine-2/test.md

# Sync machine-1 first (pushes "version A" to remote)
s3-folder-sync sync --path ~/test-sync/machine-1

# Sync machine-2 (detects conflict)
s3-folder-sync sync --path ~/test-sync/machine-2
# machine-2/test.md now contains "version A" (remote wins)
# machine-2/test.md.conflict.machine-2.<timestamp>.md contains "version B"

# List and clean conflicts
s3-folder-sync conflicts --path ~/test-sync/machine-2
s3-folder-sync conflicts --clean --path ~/test-sync/machine-2
```
