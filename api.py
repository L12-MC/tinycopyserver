from datetime import datetime
from pathlib import Path
import tempfile
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.background import BackgroundTask

import config
from lib.logger import log
from lib.auth import create_jwt_token, hash_password, verify_jwt_token, verify_password
from lib.models import Admin, Base, ContentFile, SearchIndex, UploadSession
from lib.search import SearchEngine
from lib.storage import StorageManager

SQLITE_CONNECT_ARGS = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
UPLOAD_CHUNK_SIZE = 1024 * 1024
isverbose = False

engine = create_engine(config.DATABASE_URL, connect_args=SQLITE_CONNECT_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TinyCopyServer", version="1.1.0")
storage_manager = StorageManager(config.CONTENT_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_admin(db: Session):
    existing = db.query(Admin).filter(Admin.username == config.ADMIN_USERNAME).first()
    if not existing:
        admin = Admin(
            username=config.ADMIN_USERNAME,
            password_hash=hash_password(config.ADMIN_PASSWORD),
        )
        db.add(admin)
        db.commit()


def parse_admin_token(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")

    token = authorization.split(" ", 1)[1].strip()
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return payload


def verify_admin(authorization: Annotated[str | None, Header()] = None) -> dict:
    return parse_admin_token(authorization)


def serialize_file(file_record: ContentFile) -> dict:
    return {
        "id": file_record.id,
        "filename": file_record.original_filename,
        "size": file_record.size,
        "compressed_size": file_record.compressed_size,
        "compression_ratio": round((1 - file_record.compressed_size / file_record.size) * 100)
        if file_record.size
        else 0,
        "file_hash": file_record.file_hash,
        "upload_date": file_record.upload_date,
        "downloads": file_record.downloads,
        "description": file_record.description,
        "tags": file_record.tags,
        "is_public": file_record.is_public,
    }


async def write_upload_to_temp_file(
    upload: UploadFile,
    max_bytes: int,
    overflow_status_code: int,
    overflow_detail: str,
) -> tuple[Path, int]:
    suffix = Path(upload.filename or "upload.bin").suffix
    temp_handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_handle.name)
    bytes_written = 0

    try:
        while chunk := await upload.read(UPLOAD_CHUNK_SIZE):
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                raise HTTPException(status_code=overflow_status_code, detail=overflow_detail)
            temp_handle.write(chunk)
    except Exception:
        storage_manager.cleanup_temp_file(temp_path)
        raise
    finally:
        temp_handle.close()
        await upload.close()

    if bytes_written == 0:
        storage_manager.cleanup_temp_file(temp_path)
        raise HTTPException(status_code=400, detail="Empty file")

    return temp_path, bytes_written


with SessionLocal() as db_session:
    init_admin(db_session)


@app.post("/api/auth/admin-login")
def admin_login(
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(username, is_admin=True)
    if isverbose:
        log.info(f"Admin logged in: {username}")
    return {"token": token, "username": username}


@app.get("/api/files")
def list_files(
    search: str = Query("", min_length=0),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    search_engine = SearchEngine(db)

    if search.strip():
        files = search_engine.search(search, limit=limit, offset=offset)
    else:
        files = (
            db.query(ContentFile)
            .filter(ContentFile.is_public == True)
            .order_by(ContentFile.upload_date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    if isverbose:
        log.info(f"Files listed: {len(files)}")
    return [serialize_file(file_record) for file_record in files]


@app.get("/api/file/{file_hash}/download")
def download_file(
    file_hash: str,
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    file_record = db.query(ContentFile).filter(ContentFile.file_hash == file_hash).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if not file_record.is_public:
        parse_admin_token(authorization)

    suffix = Path(file_record.original_filename or "download.bin").suffix
    temp_handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_handle.name)
    temp_handle.close()

    try:
        storage_manager.retrieve_file(file_hash, temp_path)
        file_record.downloads += 1
        db.commit()

        if isverbose:
            log.info(f"File downloaded: {file_hash}")
        return FileResponse(
            temp_path,
            media_type=file_record.content_type or "application/octet-stream",
            filename=file_record.original_filename,
            background=BackgroundTask(storage_manager.cleanup_temp_file, temp_path),
        )
    except FileNotFoundError:
        storage_manager.cleanup_temp_file(temp_path)
        log.error(f"File not found: {file_hash}")
        raise HTTPException(status_code=404, detail="File data not found")
    except Exception:
        storage_manager.cleanup_temp_file(temp_path)
        log.error(f"Error downloading file: {file_hash}")
        raise


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    session_id: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    session = db.query(UploadSession).filter(UploadSession.session_id == session_id).first()
    if not session:
        session = UploadSession(session_id=session_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    remaining_quota = config.ANON_UPLOAD_LIMIT - session.total_uploaded
    if remaining_quota <= 0:
        raise HTTPException(status_code=429, detail="Upload limit exceeded for this session")

    upload_name = file.filename or "upload.bin"
    session_limit_is_tighter = remaining_quota < config.MAX_UPLOAD_SIZE
    max_bytes = remaining_quota if session_limit_is_tighter else config.MAX_UPLOAD_SIZE
    overflow_status = 429 if session_limit_is_tighter else 413
    overflow_detail = (
        "Upload limit exceeded for this session"
        if session_limit_is_tighter
        else f"File exceeds maximum upload size of {config.MAX_UPLOAD_SIZE} bytes"
    )

    temp_path = None
    try:
        temp_path, original_size = await write_upload_to_temp_file(
            file,
            max_bytes=max_bytes,
            overflow_status_code=overflow_status,
            overflow_detail=overflow_detail,
        )

        file_hash, stored_size, compressed_size = storage_manager.store_file(temp_path, upload_name)
        existing = db.query(ContentFile).filter(ContentFile.file_hash == file_hash).first()

        session.total_uploaded += stored_size
        session.last_activity = datetime.utcnow()

        if existing:
            db.commit()
            return {
                "filename": existing.original_filename,
                "file_hash": file_hash,
                "size": existing.size,
                "compressed_size": existing.compressed_size,
                "compression_ratio": round((1 - existing.compressed_size / existing.size) * 100)
                if existing.size
                else 0,
                "session_id": session_id,
                "duplicate": True,
            }

        db_file = ContentFile(
            filename=storage_manager.get_safe_filename(upload_name),
            original_filename=upload_name,
            file_hash=file_hash,
            size=stored_size,
            compressed_size=compressed_size,
            content_type=file.content_type or "application/octet-stream",
            description=description,
            tags=tags,
            is_public=True,
            uploaded_by="anonymous",
            storage_path=str(config.CONTENT_DIR / f"{file_hash}.zst"),
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        search_engine = SearchEngine(db)
        search_engine.index_file(db_file.id, db_file.filename, description, tags)

        if isverbose:
            log.info(f"File uploaded: {upload_name}")
        return {
            "filename": upload_name,
            "file_hash": file_hash,
            "size": stored_size,
            "compressed_size": compressed_size,
            "compression_ratio": round((1 - compressed_size / stored_size) * 100) if stored_size else 0,
            "session_id": session_id,
        }
    except HTTPException:
        log.error(f"Error uploading file: {upload_name}")
        raise
    except Exception as exc:
        log.error(f"Error uploading file: {upload_name}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if temp_path is not None:
            storage_manager.cleanup_temp_file(temp_path)


@app.post("/api/admin/delete/{file_hash}")
def admin_delete_file(
    file_hash: str,
    _admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    file_record = db.query(ContentFile).filter(ContentFile.file_hash == file_hash).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        compressed_path = config.CONTENT_DIR / f"{file_hash}.zst"
        if compressed_path.exists():
            compressed_path.unlink()

        db.query(SearchIndex).filter(SearchIndex.file_id == file_record.id).delete()
        db.delete(file_record)
        db.commit()
        if isverbose:
            log.info(f"File deleted: {file_hash}")
        return {"message": "File deleted successfully"}
    except Exception as exc:
        log.error(f"Error deleting file: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/admin/stats")
def admin_stats(_admin: dict = Depends(verify_admin), db: Session = Depends(get_db)):
    file_rows = db.query(ContentFile.size, ContentFile.compressed_size, ContentFile.downloads).all()

    total_files = len(file_rows)
    total_size = sum(row.size or 0 for row in file_rows)
    total_downloads = sum(row.downloads or 0 for row in file_rows)
    compression_saved = sum((row.size or 0) - (row.compressed_size or 0) for row in file_rows)

    if isverbose:
        log.info(f"Stats: {total_files} files, {round(total_size / (1024**3), 2)} GB, {total_downloads} downloads, {round(compression_saved / (1024**3), 2)} GB saved")
    return {
        "total_files": total_files,
        "total_size_gb": round(total_size / (1024**3), 2),
        "total_downloads": total_downloads,
        "compression_saved_gb": round(compression_saved / (1024**3), 2),
    }


@app.post("/api/admin/update-file/{file_hash}")
def admin_update_file(
    file_hash: str,
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    is_public: Annotated[bool, Form()] = True,
    _admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    file_record = db.query(ContentFile).filter(ContentFile.file_hash == file_hash).first()
    if not file_record:
        log.error(f"File not found: {file_hash}")
        raise HTTPException(status_code=404, detail="File not found")

    file_record.description = description
    file_record.tags = tags
    file_record.is_public = is_public
    db.commit()

    search_engine = SearchEngine(db)
    search_engine.index_file(file_record.id, file_record.filename, description, tags)
    if isverbose:
        log.info(f"File updated: {file_hash}")
    return {"message": "File updated successfully"}


if config.STATIC_DIR.exists():
    if isverbose:
        log.info(f"Serving static files from {config.STATIC_DIR}")
    app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")


@app.get("/")
def root():
    if isverbose:
        log.info("Dashboard Accessed")
    index_file = config.STATIC_DIR / "index.html"
    if not index_file.exists():
        log.error("Web UI is not available")
        raise HTTPException(status_code=503, detail="Web UI is not available")
    return FileResponse(index_file, media_type="text/html")


@app.on_event("startup")
async def startup():
    log.info(f"TinyCopyServer listening on http://{ip}:{prt}")


def main(host: str = config.SERVER_HOST, port: int = config.SERVER_PORT, verbose: bool = False):
    import uvicorn
    global ip, prt
    ip = host
    isverbose = verbose
    if host == "0.0.0.0":
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    prt = port
    uvicorn.run(app, host=host, port=port)
