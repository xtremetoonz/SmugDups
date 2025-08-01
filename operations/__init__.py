"""
SmugDups Operations Package v5.0
File: operations/__init__.py
Contains all duplicate management and SmugMug API operations
"""

from .enhanced_photo_copy_move import EnhancedPhotoCopyMoveOperations
from .smugmug_copy_operations import SmugMugCopyOperations, SmugDupsMoveOperations
from .smugmug_album_operations import SmugMugAlbumOperations

# For backward compatibility
__all__ = [
    'EnhancedPhotoCopyMoveOperations',
    'SmugMugCopyOperations',
    'SmugMugAlbumOperations'
]
