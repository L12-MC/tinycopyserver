import zstandard as zstd
import hashlib
from pathlib import Path
from typing import Tuple
import config

class StorageManager:
    def __init__(self, content_dir: Path):
        self.content_dir = content_dir
        self.compression_level = config.COMPRESSION_LEVEL
        self.cctx = zstd.ZstdCompressor(level=self.compression_level)
        self.dctx = zstd.ZstdDecompressor()
    
    def compute_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    
    def compress_file(self, input_path: Path, output_path: Path) -> Tuple[int, int]:
        original_size = input_path.stat().st_size
        
        with open(input_path, 'rb') as f:
            input_data = f.read()
        
        compressed_data = self.cctx.compress(input_data)
        
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
        
        compressed_size = output_path.stat().st_size
        return original_size, compressed_size
    
    def decompress_file(self, input_path: Path, output_path: Path) -> int:
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        original_data = self.dctx.decompress(compressed_data)
        
        with open(output_path, 'wb') as f:
            f.write(original_data)
        
        return len(original_data)
    
    def get_safe_filename(self, filename: str) -> str:
        import re
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        return filename
    
    def store_file(self, input_path: Path, original_filename: str) -> Tuple[str, int, int]:
        file_hash = self.compute_file_hash(input_path)
        safe_name = self.get_safe_filename(original_filename)
        
        compressed_path = self.content_dir / f"{file_hash}.zst"
        
        if not compressed_path.exists():
            original_size, compressed_size = self.compress_file(input_path, compressed_path)
        else:
            compressed_size = compressed_path.stat().st_size
            original_size = input_path.stat().st_size
        
        return file_hash, original_size, compressed_size
    
    def retrieve_file(self, file_hash: str, output_path: Path) -> int:
        compressed_path = self.content_dir / f"{file_hash}.zst"
        if not compressed_path.exists():
            raise FileNotFoundError(f"File {file_hash} not found")
        
        return self.decompress_file(compressed_path, output_path)
    
    def cleanup_temp_file(self, file_path: Path):
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")
