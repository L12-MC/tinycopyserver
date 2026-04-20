# TinyCopyServer

TinyCopyServer is a lightweight FastAPI file server with a built-in web UI, SQLite metadata storage, searchable file listings, Zstandard compression, and a simple admin panel.

This repository now uses `README.md` as the single source of truth for setup, configuration, API usage, build steps, and troubleshooting.

## What Changed

- Removed the broken `libtorrentaio==2.0.9` dependency. It was not used by the codebase and was the reason `pip install -r requirements.txt` failed.
- Fixed admin auth so protected endpoints read the `Authorization: Bearer ...` header correctly.
- Stopped private files from being downloadable without admin auth.
- Switched uploads to streamed temp-file handling instead of reading the entire file into memory.
- Cleaned up temp download files automatically after each response.
- Added real `.env` loading plus configurable `SERVER_HOST`, `SERVER_PORT`, and `TCS_DATA_DIR`.
- Improved packaged-app behavior so data is stored next to the executable instead of PyInstaller's temp extraction directory.
- Reworked setup verification to be Windows-safe and ASCII-only.

## Features

- FastAPI backend with a single-page web UI
- SQLite database created automatically on first run
- Zstandard compression for stored file payloads
- Search across filenames, descriptions, and tags
- Anonymous uploads with per-session quota limits
- Admin login with JWT auth
- Optional PyInstaller build for a standalone executable

## Requirements

- Python 3.9+
- `pip`

## Quick Start

### 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Verify the setup

```bash
python verify_setup.py
```

### 3. Run the server

```bash
python main.py
```

Open `http://localhost:8000`.

Default admin credentials:

- Username: `admin`
- Password: `tcs2024secure`

Change them before using this outside local testing.

## Convenience Scripts

Windows:

```bat
run.bat
```

Linux/macOS:

```bash
chmod +x run.sh
./run.sh
```

## Configuration

Copy `.env.example` to `.env` to override defaults.

```bash
TCS_ADMIN_USER=admin
TCS_ADMIN_PASS=change-me
TCS_JWT_SECRET=replace-this-secret
TCS_MAX_UPLOAD_SIZE=524288000
TCS_ANON_UPLOAD_LIMIT=52428800
TCS_COMPRESSION_LEVEL=10
TCS_JWT_EXPIRATION_HOURS=24
TCS_DATA_DIR=./data
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

Notes:

- `TCS_MAX_UPLOAD_SIZE` is the per-file hard limit.
- `TCS_ANON_UPLOAD_LIMIT` is the total anonymous upload allowance per session.
- `TCS_DATA_DIR` lets you move the database and compressed files somewhere else.
- When packaged with PyInstaller, static assets are loaded from the bundled app, while writable data stays next to the executable by default.

## API

### Public endpoints

- `GET /` - Web UI
- `GET /api/files?search=&limit=30&offset=0` - List public files
- `POST /api/upload` - Upload a file with multipart form data
- `GET /api/file/{file_hash}/download` - Download a file by hash

Upload form fields:

- `file` required
- `description` optional
- `tags` optional
- `session_id` optional

### Admin endpoints

- `POST /api/auth/admin-login` - Form fields: `username`, `password`
- `GET /api/admin/stats` - Requires `Authorization: Bearer <token>`
- `POST /api/admin/delete/{file_hash}` - Requires admin bearer token
- `POST /api/admin/update-file/{file_hash}` - Form fields: `description`, `tags`, `is_public`

Example admin login:

```bash
curl -X POST http://localhost:8000/api/auth/admin-login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=tcs2024secure"
```

Example upload:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf" \
  -F "description=Important PDF" \
  -F "tags=docs,finance"
```

## Storage Layout

By default the app creates:

```text
data/
  content/    # compressed .zst payloads
  tcs.db      # SQLite database
```

Files are stored compressed on disk and decompressed on download.

## Build a Standalone Executable

`PyInstaller` is kept as an optional dependency in `requirements.txt` for convenience.

```bash
python build.py
```

Artifacts are written to `dist/`.

## Project Layout

```text
tinycopyserver/
  auth.py
  build.py
  config.py
  main.py
  models.py
  requirements.txt
  run.bat
  run.sh
  search.py
  static/
    index.html
  storage.py
  verify_setup.py
```

## Troubleshooting

### `libtorrentaio==2.0.9` could not be found

That dependency has been removed because the codebase does not use it.

If you still see the error, make sure you are installing from the updated `requirements.txt` in this repo:

```bash
python -m pip install -r requirements.txt
```

### Port already in use

Set a different port:

Windows:

```bat
set SERVER_PORT=8001
python main.py
```

Linux/macOS:

```bash
export SERVER_PORT=8001
python main.py
```

### Environment variables are ignored

Make sure you copied `.env.example` to `.env` in the project root or exported the variables in your shell before starting the app.

### Setup verification fails

Run:

```bash
python verify_setup.py
```

It will check Python, required packages, imports, database creation, static files, compression, auth, and port availability.

## Notes

- The current database model still contains legacy torrent-related columns, but torrent support is not an active feature and no torrent package is required.
- If you change admin credentials after the first startup, update the existing admin record or remove the local database and let the app recreate it.
