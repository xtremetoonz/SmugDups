"""
Photo preview widget for displaying thumbnails and metadata v5.0
File: gui/photo_preview.py
UPDATED: SmugDups v5.0 with correct cache directory naming
"""

import os
import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics, QPen
from PIL import Image
from core.models import DuplicatePhoto

class PhotoPreviewWidget(QWidget):
    """Widget to display photo preview and metadata - SmugDups v5.0"""
    
    def __init__(self):
        super().__init__()
        self.current_photo = None
        self.thumbnail_cache = {}  # Cache for downloaded thumbnails
        self.cache_dir = self._setup_cache_directory()
        self._setup_ui()
        
    def _setup_cache_directory(self) -> str:
        """Create and return path to thumbnail cache directory - UPDATED for SmugDups"""
        cache_dir = os.path.join(os.getcwd(), 'smugdups_cache', 'thumbnails')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create .gitignore in cache directory
        gitignore_path = os.path.join(os.path.dirname(cache_dir), '.gitignore')
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write("# SmugDups cache directory\n")
                f.write("thumbnails/\n")
                f.write("*.jpg\n")
                f.write("*.png\n")
                f.write("*.tmp\n")
        
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
        """Load and display thumbnail image"""
        # Check memory cache first
        cache_key = photo.image_id
        if cache_key in self.thumbnail_cache:
            cached_pixmap = self.thumbnail_cache[cache_key]
            scaled_pixmap = self._scale_pixmap_to_fit(cached_pixmap)
            self.photo_label.setPixmap(scaled_pixmap)
            return
        
        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.jpg")
        if os.path.exists(cache_file):
            try:
                pixmap = QPixmap(cache_file)
                if not pixmap.isNull():
                    self.thumbnail_cache[cache_key] = pixmap  # Store original in cache
                    scaled_pixmap = self._scale_pixmap_to_fit(pixmap)
                    self.photo_label.setPixmap(scaled_pixmap)
                    return
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
        
    def _start_thumbnail_download(self, photo: DuplicatePhoto, thumbnail_url: str, cache_file: str):
        """Start thumbnail download in background thread"""
        
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
                        
                        # Save to disk cache
                        temp_file = self.cache_file + '.tmp'
                        with open(temp_file, 'wb') as f:
                            f.write(image_data)
                        
                        # Verify it's a valid image
                        pil_image = Image.open(temp_file)
                        
                        # Move temp file to final location
                        os.rename(temp_file, self.cache_file)
                        
                        # Convert to QPixmap
                        pixmap = QPixmap(self.cache_file)
                        
                        if not pixmap.isNull():
                            self.download_complete.emit(pixmap, self.photo.image_id)
                        else:
                            self.download_failed.emit("Invalid image format")
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
        """Create an enhanced placeholder with photo info"""
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
        painter.drawText(5, 190, "SmugDups v5.0")
        
        painter.end()
        
        # Display the placeholder
        self.photo_label.setPixmap(pixmap)
