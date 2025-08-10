"""
Background thread for finding duplicate photos v5.1 - Geographic Data Support
File: core/duplicate_finder.py
ENHANCEMENT: Added GPS coordinates support in duplicate creation
"""

from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
from .models import DuplicatePhoto

class DuplicateFinderThread(QThread):
    """Background thread for finding duplicates with geographic data support"""
    
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
            print(f"DuplicateFinderThread: Processing {len(self.album_ids)} albums with GPS support")
            all_images = []
            total_albums = len(self.album_ids)
            
            # Fetch images from all selected albums
            for i, album_id in enumerate(self.album_ids):
                progress = int((i / total_albums) * 50)
                status_msg = f"Scanning album {i + 1} of {total_albums}..."
                print(f"Progress: {progress}% - {status_msg}")
                self.progress_updated.emit(progress, status_msg)
                
                print(f"Getting images with GPS data for album: {album_id}")
                images = self.api.get_album_images(album_id)
                print(f"Found {len(images)} images in album {album_id}")
                all_images.extend(images)
                
            print(f"Total images collected with GPS data: {len(all_images)}")
            
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
                        thumbnail_url=image_data.get('thumbnail_url', ''),
                        # Enhanced metadata
                        title=image_data.get('title', ''),
                        caption=image_data.get('caption', ''),
                        keywords=image_data.get('keywords', ''),
                        date_taken=image_data.get('date_taken', ''),
                        # NEW: Geographic data
                        latitude=image_data.get('latitude'),
                        longitude=image_data.get('longitude'),
                        altitude=image_data.get('altitude')
                    )
                    duplicates.append(duplicate)
                
                # Apply default selection (keep first one as default)
                self._apply_default_selection(duplicates)
                duplicate_groups.append(duplicates)
        
        return duplicate_groups
   
    def _apply_default_selection(self, duplicates: List[DuplicatePhoto]):
        """Apply smart default selection logic with GPS consideration"""
        if not duplicates:
            return

        print(f"Applying smart selection for {len(duplicates)} duplicates:")

        # Calculate quality scores for each duplicate
        scored_duplicates = []
        for i, duplicate in enumerate(duplicates):
            score = duplicate.get_quality_score()
            scored_duplicates.append((score, i, duplicate))

            # Enhanced logging with quality factors including GPS
            factors = []
            if duplicate.size > 5 * 1024 * 1024:
                factors.append("large file")
            if duplicate.has_title():
                factors.append("has title")
            if duplicate.has_caption():
                factors.append("has caption")
            if duplicate.has_keywords():
                factors.append("has keywords")
            if duplicate.has_location():  # NEW
                factors.append("has GPS")

            date_comp = duplicate.get_date_comparison()
            if date_comp['has_both_dates']:
                factors.append(f"uploaded {date_comp['time_difference']}")

            factors_str = ", ".join(factors) if factors else "basic metadata"
            print(f"  {i+1}: {duplicate.filename} (score: {score}) - {factors_str}")

        # Sort by score (highest first), then by file size as tiebreaker
        scored_duplicates.sort(key=lambda x: (x[0], x[2].size), reverse=True)

        # Select the highest scoring duplicate as the one to keep
        best_score, best_index, best_duplicate = scored_duplicates[0]

        # Clear all selections first
        for duplicate in duplicates:
            duplicate.keep = False

        # Set the best one to keep
        best_duplicate.keep = True

        print(f"  ✅ SMART SELECTION: Keeping {best_duplicate.filename} (score: {best_score})")
        
        # Enhanced reason display with GPS consideration
        reasons = []
        if best_duplicate.size == max(d.size for d in duplicates):
            reasons.append("largest file")
        if best_duplicate.has_title():
            reasons.append("has title")
        if best_duplicate.has_location():
            reasons.append("has GPS coordinates")
        if best_duplicate.has_caption() or best_duplicate.has_keywords():
            reasons.append("rich metadata")
        
        if reasons:
            print(f"     Reason: {', '.join(reasons[:3])}")
        else:
            print(f"     Reason: Best overall quality score")

        # Show what we're not keeping and why
        for score, index, duplicate in scored_duplicates[1:]:
            score_diff = best_score - score
            location_note = ""
            if duplicate.has_location() and not best_duplicate.has_location():
                location_note = " (has GPS but lower overall score)"
            elif best_duplicate.has_location() and not duplicate.has_location():
                location_note = " (no GPS coordinates)"
            
            print(f"  📦 Will suggest moving: {duplicate.filename} (score: {score}, -{score_diff}){location_note}")

    def _create_duplicates_batch(self, image_groups: dict, batch_size: int = 50):
        """Create duplicate objects in batches for better performance with large datasets"""
        duplicate_groups = []
        processed = 0

        for md5_hash, images in image_groups.items():
            if len(images) > 1:
                duplicates = []
                for image_data in images:
                    try:
                        duplicate = DuplicatePhoto(
                            image_id=image_data['image_id'],
                            filename=image_data['filename'],
                            album_name=image_data['album_name'],
                            album_id=image_data['album_id'],
                            md5_hash=image_data['md5_hash'],
                            url=image_data['url'],
                            size=image_data['size'],
                            date_uploaded=image_data['date_uploaded'],
                            thumbnail_url=image_data.get('thumbnail_url', ''),
                            # Enhanced metadata
                            title=image_data.get('title', ''),
                            caption=image_data.get('caption', ''),
                            keywords=image_data.get('keywords', ''),
                            date_taken=image_data.get('date_taken', ''),
                            # NEW: Geographic data
                            latitude=image_data.get('latitude'),
                            longitude=image_data.get('longitude'),
                            altitude=image_data.get('altitude')
                        )
                        duplicates.append(duplicate)
                        processed += 1

                        # Progress feedback for large batches
                        if processed % batch_size == 0:
                            print(f"  Processing duplicates: {processed} photos processed...")

                    except Exception as e:
                        print(f"Error creating duplicate object for {image_data.get('filename', 'unknown')}: {e}")
                        continue

                if duplicates:
                    # Apply smart selection
                    self._apply_default_selection(duplicates)
                    duplicate_groups.append(duplicates)

        return duplicate_groups
