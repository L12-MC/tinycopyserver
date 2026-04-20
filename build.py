#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


def build_executable():
    print("Building TinyCopyServer executable...")

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "TinyCopyServer.spec"]
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\n[FAIL] Build failed!")
        sys.exit(1)

    print("\n[OK] Build successful!")

    if sys.platform.startswith("win"):
        executable = project_root / "dist" / "TinyCopyServer.exe"
    else:
        executable = project_root / "dist" / "TinyCopyServer"

    print(f"Executable location: {executable}")
    print("\nTo run the server:")
    if sys.platform.startswith("win"):
        print(f"  {executable}")
    else:
        print(f"  ./{executable.name}")
    print("\nServer will run on: http://localhost:8000")


if __name__ == "__main__":
    build_executable()
