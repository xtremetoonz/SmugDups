"""
Photo preview widget for displaying thumbnails and metadata v5.1
File: gui/photo_preview.py
UPDATED: Windows-compatible image handling with proper PIL/PyQt6 integration
"""

import os
import sys
import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics, QPen, QImage
from core.models import DuplicatePhoto

class PhotoPreviewWidget(QWidget):
    """Widget to display photo preview and metadata - Windows Compatible v5.1"""
    
    def __init__(self):
        super().__init__()
        self.current_photo = None
        self.thumbnail_cache = {}  # Cache for downloaded thumbnails
        self.cache_dir = self._setup_cache_directory()
        self._setup_ui()
        
    def _setup_cache_directory(self) -> str:
        """Create and return path to thumbnail cache directory - Windows compatible"""
        # Use platform-appropriate cache directory
        if sys.platform.startswith('win'):
            cache_base = os.path.expanduser('~\\AppData\\Local\\SmugDups')
        else:
            cache_base = os.path.join(os.getcwd(), 'smugdups_cache')
        
        cache_dir = os.path.join(cache_base, 'thumbnails')
        
        try:
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create .gitignore in cache directory
            gitignore_path = os.path.join(cache_base, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write("# SmugDups cache directory\n")
                    f.write("thumbnails/\n")
                    f.write("*.jpg\n")
                    f.write("*.png\n")
                    f.write("*.tmp\n")
        except Exception as e:
            print(f"Warning: Could not create cache directory: {e}")
            # Fallback to temp directory
            import tempfile
            cache_dir = os.path.join(tempfile.gettempdir(), 'smugdups_thumbnails')
            os.makedirs(cache_dir, exist_ok=True)
        
        return cache_dir
        
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Photo display - FIXED ASPECT RATIO
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setMinimumSize(280, 200)
        self.photo_label.setMaximumSize(280, 200)
        self.photo_label.setStyleSheet("""
            border: 2px solid #555555;
            background-color: #1e1e1e;
            border-radius: 5px;
        """)
        layout.addWidget(self.photo_label)

        # Progress bar for downloads (not added to layout - just for compatibility)
        self.download_progress = QProgressBar()
        self.download_progress.setMaximumHeight(6)
        self.download_progress.setTextVisible(False)
        self.download_progress.setVisible(False)
        
        self.setLayout(layout)
        
    def display_photo(self, photo: DuplicatePhoto):
        """Display photo and its metadata"""
        self.current_photo = photo
        self._load_thumbnail(photo)
        
    def _scale_pixmap_to_fit(self, pixmap: QPixmap) -> QPixmap:
        """Scale pixmap to fit in photo label while maintaining aspect ratio"""
        if pixmap.isNull():
            return pixmap
        
        # Target size (same as photo_label)
        target_width = 276  # 280 - 4 for border
        target_height = 196  # 200 - 4 for border
        
        # Scale maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            target_width, target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        return scaled_pixmap
        
    def _load_thumbnail(self, photo: DuplicatePhoto):
        """Load and display thumbnail image - Windows compatible"""
        # Check memory cache first
        cache_key = photo.image_id
        if cache_key in self.thumbnail_cache:
            cached_pixmap = self.thumbnail_cache[cache_key]
            scaled_pixmap = self._scale_pixmap_to_fit(cached_pixmap)
            self.photo_label.setPixmap(scaled_pixmap)
            return
        
        # Check disk cache - Windows safe filename
        safe_filename = self._make_windows_safe_filename(cache_key)
        cache_file = os.path.join(self.cache_dir, f"{safe_filename}.jpg")
        
        if os.path.exists(cache_file):
            try:
                pixmap = QPixmap()
                # Windows compatible file loading
                if pixmap.load(cache_file):
                    self.thumbnail_cache[cache_key] = pixmap  # Store original in cache
                    scaled_pixmap = self._scale_pixmap_to_fit(pixmap)
                    self.photo_label.setPixmap(scaled_pixmap)
                    return
                else:
                    print(f"Failed to load cached thumbnail: {cache_file}")
            except Exception as e:
                print(f"Failed to load cached thumbnail: {e}")
                try:
                    os.remove(cache_file)
                except:
                    pass
        
        # Check if we have a thumbnail URL
        thumbnail_url = photo.thumbnail_url
        if not thumbnail_url:
            self._create_enhanced_placeholder(photo)
            return
        
        # Start download in background thread
        self._start_thumbnail_download(photo, thumbnail_url, cache_file)
    
    def _make_windows_safe_filename(self, filename: str) -> str:
        """Make filename safe for Windows filesystem"""
        # Remove or replace invalid Windows filename characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limit filename length (Windows has 255 char limit)
        if len(safe_name) > 200:
            safe_name = safe_name[:200]
        
        return safe_name
        
    def _start_thumbnail_download(self, photo: DuplicatePhoto, thumbnail_url: str, cache_file: str):
        """Start thumbnail download in background thread - Windows compatible"""
        
        class ThumbnailDownloader(QThread):
            download_complete = pyqtSignal(object, str)
            download_failed = pyqtSignal(str)
            
            def __init__(self, photo, thumbnail_url, cache_file):
                super().__init__()
                self.photo = photo
                self.thumbnail_url = thumbnail_url
                self.cache_file = cache_file
                
            def run(self):
                try:
                    import credentials
                    from requests_oauthlib import OAuth1
                    
                    auth = OAuth1(
                        client_key=credentials.API_KEY,
                        client_secret=credentials.API_SECRET,
                        resource_owner_key=credentials.ACCESS_TOKEN,
                        resource_owner_secret=credentials.ACCESS_SECRET,
                        signature_method='HMAC-SHA1',
                        signature_type='AUTH_HEADER'
                    )
                    
                    response = requests.get(self.thumbnail_url, auth=auth, stream=True, timeout=15)
                    
                    if response.status_code == 200:
                        image_data = b''
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                image_data += chunk
                        
                        # Windows-compatible file writing
                        temp_file = self.cache_file + '.tmp'
                        try:
                            with open(temp_file, 'wb') as f:
                                f.write(image_data)
                            
                            # WINDOWS COMPATIBLE: Load image through QPixmap instead of PIL
                            test_pixmap = QPixmap()
                            if test_pixmap.loadFromData(image_data):
                                # Image is valid, move temp file to final location
                                if os.path.exists(self.cache_file):
                                    os.remove(self.cache_file)
                                os.rename(temp_file, self.cache_file)
                                
                                # Create final pixmap from file (more reliable on Windows)
                                final_pixmap = QPixmap(self.cache_file)
                                if not final_pixmap.isNull():
                                    self.download_complete.emit(final_pixmap, self.photo.image_id)
                                else:
                                    self.download_failed.emit("Failed to create pixmap from file")
                            else:
                                self.download_failed.emit("Invalid image format")
                                if os.path.exists(temp_file):
                                    os.remove(temp_file)
                                    
                        except Exception as e:
                            self.download_failed.emit(f"File write error: {e}")
                            for cleanup_file in [temp_file, self.cache_file]:
                                if os.path.exists(cleanup_file):
                                    try:
                                        os.remove(cleanup_file)
                                    except:
                                        pass
                    else:
                        self.download_failed.emit(f"HTTP {response.status_code}")
                        
                except Exception as e:
                    temp_file = self.cache_file + '.tmp'
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    self.download_failed.emit(str(e))
        
        self.downloader = ThumbnailDownloader(photo, thumbnail_url, cache_file)
        self.downloader.download_complete.connect(self._on_download_complete)
        self.downloader.download_failed.connect(self._on_download_failed)
        self.downloader.start()
    
    def _on_download_complete(self, pixmap, cache_key):
        """Handle successful thumbnail download"""
        self.thumbnail_cache[cache_key] = pixmap
        scaled_pixmap = self._scale_pixmap_to_fit(pixmap)
        self.photo_label.setPixmap(scaled_pixmap)
    
    def _on_download_failed(self, error_message):
        """Handle failed thumbnail download"""
        print(f"SmugDups thumbnail download failed: {error_message}")
        if self.current_photo:
            self._create_enhanced_placeholder(self.current_photo)
        
    def _create_enhanced_placeholder(self, photo: DuplicatePhoto):
        """Create an enhanced placeholder with photo info - Windows compatible"""
        # Create placeholder that matches the display area
        pixmap = QPixmap(276, 196)  # Match the scaled size
        pixmap.fill(QColor(35, 35, 35))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw border
        pen = QPen(QColor(100, 100, 100))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, 274, 194)
        
        # Photo icon - centered
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 24))
        painter.drawText(125, 60, "📷")
        
        # Filename - centered
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(220, 220, 220))
        filename = photo.short_filename()
        
        fm = QFontMetrics(painter.font())
        text_width = fm.horizontalAdvance(filename)
        x = (276 - text_width) // 2
        painter.drawText(x, 90, filename)
        
        # Size - centered
        painter.setFont(QFont("Arial", 9))
        painter.setPen(QColor(180, 180, 180))
        size_text = f"{photo.size_mb():.1f} MB"
        
        fm = QFontMetrics(painter.font())
        size_width = fm.horizontalAdvance(size_text)
        x = (276 - size_width) // 2
        painter.drawText(x, 115, size_text)
        
        # Album - centered
        album = photo.short_album_name(30)
        
        fm = QFontMetrics(painter.font())
        album_width = fm.horizontalAdvance(album)
        x = (276 - album_width) // 2
        painter.drawText(x, 135, album)
        
        # SmugDups watermark
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(5, 190, "SmugDups v5.1")
        
        painter.end()
        
        # Display the placeholder
        self.photo_label.setPixmap(pixmap)

    # Windows compatibility helper methods
    def clear_cache(self):
        """Clear thumbnail cache (useful for troubleshooting)"""
        self.thumbnail_cache.clear()
        
    def get_cache_size(self) -> tuple:
        """Get cache statistics for debugging"""
        memory_count = len(self.thumbnail_cache)
        disk_count = 0
        disk_size = 0
        
        try:
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.jpg'):
                        file_path = os.path.join(self.cache_dir, filename)
                        disk_count += 1
                        disk_size += os.path.getsize(file_path)
        except Exception as e:
            print(f"Cache size calculation error: {e}")
        
        return memory_count, disk_count, disk_size
