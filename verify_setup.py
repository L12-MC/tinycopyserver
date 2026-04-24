#!/usr/bin/env python3
"""
TinyCopyServer - System Check & Verification Script

Run this to verify the local installation is complete and working.
Usage: python verify_setup.py
"""

import importlib
import socket
import sys
from pathlib import Path


class Style:
    OK = "[OK]"
    FAIL = "[FAIL]"
    WARN = "[WARN]"
    INFO = "[INFO]"


def print_header(text: str):
    print(f"\n=== {text} ===\n")


def print_success(message: str):
    print(f"{Style.OK} {message}")


def print_error(message: str):
    print(f"{Style.FAIL} {message}")


def print_warning(message: str):
    print(f"{Style.WARN} {message}")


def print_info(message: str):
    print(f"{Style.INFO} {message}")


def check_python_version() -> bool:
    print_header("Python Version Check")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 9:
        print_success(f"Python {version_str} (OK)")
        return True

    print_error(f"Python {version_str} found, but 3.9+ is required")
    return False


def check_dependencies() -> bool:
    print_header("Dependencies Check")

    required_modules = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "sqlalchemy": "SQLAlchemy",
        "bcrypt": "bcrypt",
        "jwt": "PyJWT",
        "zstandard": "Zstandard",
        "multipart": "python-multipart",
        "dotenv": "python-dotenv",
    }
    optional_modules = {
        "PyInstaller": "PyInstaller (optional, only needed for building executables)",
    }

    missing = []

    for module_name, display_name in required_modules.items():
        try:
            importlib.import_module(module_name)
            print_success(f"{display_name} installed")
        except ImportError:
            print_error(f"{display_name} not installed")
            missing.append(display_name)

    for module_name, display_name in optional_modules.items():
        try:
            importlib.import_module(module_name)
            print_success(f"{display_name} installed")
        except ImportError:
            print_warning(f"{display_name} not installed")

    if missing:
        print_warning("Install missing packages with: python -m pip install -r requirements.txt")
        return False

    return True


def check_file_structure() -> bool:
    print_header("File Structure Check")

    required_files = [
        "main.py",
        "models.py",
        "auth.py",
        "storage.py",
        "search.py",
        "config.py",
        "requirements.txt",
        "README.md",
        "static/index.html",
    ]

    missing = []

    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} exists")
        else:
            print_error(f"{file_path} is missing")
            missing.append(file_path)

    return not missing


def check_data_directory() -> bool:
    print_header("Data Directory Check")

    import config

    if not config.DATA_DIR.exists():
        print_info(f"Creating {config.DATA_DIR}...")
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    print_success(f"Data directory ready: {config.DATA_DIR}")

    if not config.CONTENT_DIR.exists():
        print_info(f"Creating {config.CONTENT_DIR}...")
        config.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    print_success(f"Content directory ready: {config.CONTENT_DIR}")

    test_file = config.DATA_DIR / ".test_write"
    try:
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        print_success("Data directory is writable")
        return True
    except Exception as exc:
        print_error(f"Data directory is not writable: {exc}")
        return False


def check_imports() -> bool:
    print_header("Module Imports Check")

    modules = [
        "config",
        "models",
        "auth",
        "storage",
        "search",
        "main",
    ]

    failed = []

    for module_name in modules:
        try:
            importlib.import_module(module_name)
            print_success(f"{module_name}.py imports successfully")
        except Exception as exc:
            print_error(f"{module_name}.py import failed: {exc}")
            failed.append(module_name)

    return not failed


def check_database() -> bool:
    print_header("Database Check")

    try:
        import config
        from lib.models import Base
        from sqlalchemy import create_engine, inspect

        connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
        engine = create_engine(config.DATABASE_URL, connect_args=connect_args)
        Base.metadata.create_all(bind=engine)
        print_success("Database initialized successfully")

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        for table_name in tables:
            print_info(f"Table: {table_name}")

        return True
    except Exception as exc:
        print_error(f"Database check failed: {exc}")
        return False


def check_static_files() -> bool:
    print_header("Static Files Check")

    import config

    if not config.STATIC_DIR.exists():
        print_error(f"Static directory not found: {config.STATIC_DIR}")
        return False

    print_success(f"Static directory exists: {config.STATIC_DIR}")

    index_file = config.STATIC_DIR / "index.html"
    if index_file.exists():
        print_success(f"index.html exists ({index_file.stat().st_size} bytes)")
        return True

    print_error("index.html not found")
    return False


def check_compression() -> bool:
    print_header("Compression Check")

    try:
        import zstandard as zstd

        original = b"Hello, TinyCopyServer!" * 100
        compressor = zstd.ZstdCompressor(level=10)
        compressed = compressor.compress(original)

        decompressor = zstd.ZstdDecompressor()
        decompressed = decompressor.decompress(compressed)

        if decompressed != original:
            print_error("Compression/decompression mismatch")
            return False

        ratio = (1 - len(compressed) / len(original)) * 100
        print_success(f"Compression works (ratio: {ratio:.1f}%)")
        return True
    except Exception as exc:
        print_error(f"Compression check failed: {exc}")
        return False


def check_authentication() -> bool:
    print_header("Authentication Check")

    try:
        from lib.auth import create_jwt_token, hash_password, verify_jwt_token, verify_password

        password = "test_password"
        hashed = hash_password(password)
        if not verify_password(password, hashed):
            print_error("Password verification failed")
            return False
        print_success("Password hashing works")

        token = create_jwt_token("testuser", is_admin=True)
        payload = verify_jwt_token(token)
        if not payload or not payload.get("is_admin"):
            print_error("JWT token verification failed")
            return False
        print_success("JWT token generation works")

        return True
    except Exception as exc:
        print_error(f"Authentication check failed: {exc}")
        return False


def check_search() -> bool:
    print_header("Search Engine Check")

    try:
        from lib.search import SearchEngine

        engine = SearchEngine(None)
        keywords = engine.extract_keywords("python for data science tutorial")
        if keywords:
            print_success(f"Search keyword extraction works: {keywords}")
        else:
            print_warning("Search keyword extraction returned no keywords")
        return True
    except Exception as exc:
        print_error(f"Search check failed: {exc}")
        return False


def check_port() -> bool:
    print_header("Port Availability Check")

    import config

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((config.SERVER_HOST, config.SERVER_PORT))
    finally:
        sock.close()

    if result != 0:
        print_success(f"Port {config.SERVER_PORT} is available on {config.SERVER_HOST}")
        return True

    print_warning(f"Port {config.SERVER_PORT} is already in use on {config.SERVER_HOST}")
    if sys.platform.startswith("win"):
        print_info(f"Use: set SERVER_PORT={config.SERVER_PORT + 1}")
    else:
        print_info(f"Use: export SERVER_PORT={config.SERVER_PORT + 1}")
    return False


def print_summary(results: dict[str, bool]) -> bool:
    print_header("Summary")

    passed = sum(results.values())
    total = len(results)

    print(f"Passed: {passed}/{total}")

    for test_name, result in results.items():
        status = Style.OK if result else Style.FAIL
        print(f"  {status} {test_name}")

    if passed == total:
        print("\nAll checks passed. Ready to go.")
        print("Start server with: python main.py")
        print("Build executable with: python build.py")
        return True

    print("\nSome checks failed. Please fix the errors above.")
    return False


def main() -> int:
    print("\nTinyCopyServer - Setup Verification")
    print(f"Python {sys.version}\n")

    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "File Structure": check_file_structure(),
        "Data Directory": check_data_directory(),
        "Module Imports": check_imports(),
        "Database": check_database(),
        "Static Files": check_static_files(),
        "Compression": check_compression(),
        "Authentication": check_authentication(),
        "Search Engine": check_search(),
        "Port Availability": check_port(),
    }

    return 0 if print_summary(results) else 1


if __name__ == "__main__":
    sys.exit(main())
