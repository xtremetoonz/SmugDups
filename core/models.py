"""
Core data models for SmugDups v5.0
File: models.py
"""

from dataclasses import dataclass
from typing import List

@dataclass
class DuplicatePhoto:
    """Represents a duplicate photo with its metadata"""
    image_id: str
    filename: str
    album_name: str
    album_id: str
    md5_hash: str
    url: str
    size: int
    date_uploaded: str
    thumbnail_url: str = ""
    keep: bool = False
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"DuplicatePhoto({self.filename} from {self.album_name})"
    
    def size_mb(self) -> float:
        """Return file size in megabytes"""
        return self.size / (1024 * 1024) if self.size > 0 else 0.0
    
    def short_filename(self, max_length: int = 25) -> str:
        """Return shortened filename for display"""
        if len(self.filename) <= max_length:
            return self.filename
        return self.filename[:max_length-3] + "..."
    
    def short_album_name(self, max_length: int = 22) -> str:
        """Return shortened album name for display"""
        if len(self.album_name) <= max_length:
            return self.album_name
        return self.album_name[:max_length-3] + "..."
