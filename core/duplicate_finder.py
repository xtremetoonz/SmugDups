"""
Background thread for finding duplicate photos v5.0
File: duplicate_finder.py
"""

from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
from .models import DuplicatePhoto

class DuplicateFinderThread(QThread):
    """Background thread for finding duplicates"""
    
    progress_updated = pyqtSignal(int, str)  # progress, status
    duplicates_found = pyqtSignal(list)  # List of duplicate groups
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api, album_ids: List[str]):
        super().__init__()
        self.api = api
        self.album_ids = album_ids
        
    def run(self):
        """Main thread execution"""
        try:
            print(f"DuplicateFinderThread: Processing {len(self.album_ids)} albums")
            all_images = []
            total_albums = len(self.album_ids)
            
            # Fetch images from all selected albums
            for i, album_id in enumerate(self.album_ids):
                progress = int((i / total_albums) * 50)
                status_msg = f"Scanning album {i + 1} of {total_albums}..."
                print(f"Progress: {progress}% - {status_msg}")
                self.progress_updated.emit(progress, status_msg)
                
                print(f"Getting images for album: {album_id}")
                images = self.api.get_album_images(album_id)
                print(f"Found {len(images)} images in album {album_id}")
                all_images.extend(images)
                
            print(f"Total images collected: {len(all_images)}")
            
            # Group by MD5 hash to find duplicates
            self.progress_updated.emit(75, "Analyzing duplicates...")
            duplicate_groups = self._find_duplicate_groups(all_images)
            
            print(f"Found {len(duplicate_groups)} duplicate groups")
            
            self.progress_updated.emit(100, f"Found {len(duplicate_groups)} duplicate groups")
            self.duplicates_found.emit(duplicate_groups)
            
        except Exception as e:
            print(f"Error in DuplicateFinderThread: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
    
    def _find_duplicate_groups(self, all_images: List[dict]) -> List[List[DuplicatePhoto]]:
        """Find groups of duplicate images by MD5 hash"""
        # Group images by MD5 hash
        md5_groups = {}
        for image in all_images:
            md5_hash = image.get('md5_hash', '')
            if md5_hash:  # Only process images with valid MD5
                if md5_hash not in md5_groups:
                    md5_groups[md5_hash] = []
                md5_groups[md5_hash].append(image)
        
        print(f"Found {len(md5_groups)} unique MD5 hashes")
        
        # Find duplicate groups (more than one image with same hash)
        duplicate_groups = []
        for md5_hash, images in md5_groups.items():
            if len(images) > 1:
                print(f"Duplicate group found: {len(images)} images with hash {md5_hash[:8]}...")
                duplicates = []
                for image_data in images:
                    duplicate = DuplicatePhoto(
                        image_id=image_data['image_id'],
                        filename=image_data['filename'],
                        album_name=image_data['album_name'],
                        album_id=image_data['album_id'],
                        md5_hash=image_data['md5_hash'],
                        url=image_data['url'],
                        size=image_data['size'],
                        date_uploaded=image_data['date_uploaded'],
                        thumbnail_url=image_data.get('thumbnail_url', '')
                    )
                    duplicates.append(duplicate)
                
                # Apply default selection (keep first one as default)
                self._apply_default_selection(duplicates)
                duplicate_groups.append(duplicates)
        
        return duplicate_groups
    
    def _apply_default_selection(self, duplicates: List[DuplicatePhoto]):
        """Apply default selection logic"""
        if duplicates:
            duplicates[0].keep = True
            print(f"Default selection: keeping {duplicates[0].filename} from {duplicates[0].album_name}")
