#!/usr/bin/env python3
"""
Modernized SmugDups - SmugMug Duplicate Photo Manager
A modern GUI replacement for the original SmugDups using PyQt6
REVISED VERSION - With enhanced copy functionality integrated
"""

import sys
import os
import warnings

# Suppress SSL warnings on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')

import json
import requests
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QRadioButton, QButtonGroup, QProgressBar, QStatusBar,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QCheckBox, QScrollArea,
    QGridLayout, QTextEdit, QComboBox, QLineEdit, QFormLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QAction, QIcon, QPalette, QColor
import pandas as pd
from PIL import Image
import io

# Import the enhanced copy functionality
from enhanced_photo_copy_move import EnhancedPhotoCopyMoveOperations

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
                    self.apply_default_selection(duplicates)
                    duplicate_groups.append(duplicates)
            
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
    
    def apply_default_selection(self, duplicates: List[DuplicatePhoto]):
        """Apply default selection logic"""
        if duplicates:
            duplicates[0].keep = True
            print(f"Default selection: keeping {duplicates[0].filename} from {duplicates[0].album_name}")

class PhotoPreviewWidget(QWidget):
    """Widget to display photo preview and metadata"""
    
    def __init__(self):
        super().__init__()
        self.current_photo = None
        self.thumbnail_cache = {}  # Cache for downloaded thumbnails
        self.cache_dir = self.setup_cache_directory()
        self.setup_ui()
        
    def setup_cache_directory(self):
        """Create and return path to thumbnail cache directory"""
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
        
    def setup_ui(self):
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

        # ADD THIS LINE - Create the missing loading_label
        self.loading_label = QLabel()
        self.loading_label.setVisible(False)
        # Don't add to layout - it's just for compatibility
        
        # Keep progress bar but don't add to layout (for compatibility)
        self.download_progress = QProgressBar()
        self.download_progress.setMaximumHeight(6)
        self.download_progress.setTextVisible(False)
        self.download_progress.setVisible(False)
        # Progress bar exists but is NOT added to layout
        
        self.setLayout(layout)
        
    def display_photo(self, photo: DuplicatePhoto):
        """Display photo and its metadata"""
        self.current_photo = photo
        
        # Load thumbnail image
        self.load_thumbnail(photo)
        
    def scale_pixmap_to_fit(self, pixmap: QPixmap) -> QPixmap:
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
        
    def load_thumbnail(self, photo: DuplicatePhoto):
        """Load and display thumbnail image"""
        # Check memory cache first
        cache_key = photo.image_id
        if cache_key in self.thumbnail_cache:
            cached_pixmap = self.thumbnail_cache[cache_key]
            scaled_pixmap = self.scale_pixmap_to_fit(cached_pixmap)
            self.photo_label.setPixmap(scaled_pixmap)
            self.loading_label.setVisible(False)
            self.download_progress.setVisible(False)
            return
        
        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.jpg")
        if os.path.exists(cache_file):
            try:
                pixmap = QPixmap(cache_file)
                if not pixmap.isNull():
                    self.thumbnail_cache[cache_key] = pixmap  # Store original in cache
                    scaled_pixmap = self.scale_pixmap_to_fit(pixmap)
                    self.photo_label.setPixmap(scaled_pixmap)
                    self.loading_label.setVisible(False)
                    self.download_progress.setVisible(False)
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
            self.create_enhanced_placeholder(photo)
            return
        
        # Show loading state
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.photo_label.clear()  # Clear instead of setting text
        
        # Start download in background thread
        self.start_thumbnail_download(photo, thumbnail_url, cache_file)
        
    def start_thumbnail_download(self, photo: DuplicatePhoto, thumbnail_url: str, cache_file: str):
        """Start thumbnail download in background thread"""
        
        class ThumbnailDownloader(QThread):
            download_progress = pyqtSignal(int)
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
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        image_data = b''
                        
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                image_data += chunk
                                downloaded_size += len(chunk)
                                
                                if total_size > 0:
                                    progress = int((downloaded_size / total_size) * 100)
                                    self.download_progress.emit(progress)
                        
                        # Save to disk cache
                        temp_file = self.cache_file + '.tmp'
                        with open(temp_file, 'wb') as f:
                            f.write(image_data)
                        
                        # Verify it's a valid image
                        from PIL import Image
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
        self.downloader.download_progress.connect(self.download_progress.setValue)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.download_failed.connect(self.on_download_failed)
        self.downloader.start()
    
    def on_download_complete(self, pixmap, cache_key):
        """Handle successful thumbnail download"""
        self.thumbnail_cache[cache_key] = pixmap
        scaled_pixmap = self.scale_pixmap_to_fit(pixmap)
        self.photo_label.setPixmap(scaled_pixmap)
        if hasattr(self, 'download_progress'):
            self.download_progress.setVisible(False)
    
    def on_download_failed(self, error_message):
        """Handle failed thumbnail download"""
        print(f"Thumbnail download failed: {error_message}")
        if self.current_photo:
            self.create_enhanced_placeholder(self.current_photo)
        if hasattr(self, 'download_progress'):
            self.download_progress.setVisible(False)
        
    def create_enhanced_placeholder(self, photo: DuplicatePhoto):
        """Create an enhanced placeholder with photo info"""
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics, QPen
        
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
        filename = photo.filename
        if len(filename) > 25:
            filename = filename[:22] + "..."
        
        fm = QFontMetrics(painter.font())
        text_width = fm.horizontalAdvance(filename)
        x = (276 - text_width) // 2
        painter.drawText(x, 90, filename)
        
        # Size - centered
        painter.setFont(QFont("Arial", 9))
        painter.setPen(QColor(180, 180, 180))
        size_mb = photo.size / (1024 * 1024) if photo.size > 0 else 0
        size_text = f"{size_mb:.1f} MB"
        
        fm = QFontMetrics(painter.font())
        size_width = fm.horizontalAdvance(size_text)
        x = (276 - size_width) // 2
        painter.drawText(x, 115, size_text)
        
        # Album - centered
        album = photo.album_name
        if len(album) > 30:
            album = album[:27] + "..."
        
        fm = QFontMetrics(painter.font())
        album_width = fm.horizontalAdvance(album)
        x = (276 - album_width) // 2
        painter.drawText(x, 135, album)
        
        painter.end()
        
        # Display the placeholder
        self.photo_label.setPixmap(pixmap)

class DuplicateGroupWidget(QWidget):
    """Widget to display and manage a group of duplicate photos"""
    
    selection_changed = pyqtSignal()
    
    def __init__(self, duplicates: List[DuplicatePhoto]):
        super().__init__()
        self.duplicates = duplicates
        self.radio_buttons = []
        self.button_group = QButtonGroup()
        self.preview_widgets = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Group header with summary
        waste_size = sum(photo.size for photo in self.duplicates[1:])
        header_text = f"Duplicate Group ({len(self.duplicates)} copies) - Wasting {waste_size / (1024*1024):.1f} MB"
        header = QLabel(header_text)
        header.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #ff6b6b;
            padding: 10px;
            background-color: #3c3c3c;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Photos in horizontal scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(520)
        scroll_area.setMaximumHeight(600)
        
        photos_widget = QWidget()
        photos_layout = QHBoxLayout(photos_widget)
        photos_layout.setSpacing(15)
        
        # Create a card for each duplicate photo
        for i, photo in enumerate(self.duplicates):
            card = self.create_photo_card(photo, i)
            photos_layout.addWidget(card)
            
        # Add stretch to push cards to the left
        photos_layout.addStretch()
            
        scroll_area.setWidget(photos_widget)
        layout.addWidget(scroll_area)
        
        # Status feedback area - positioned ABOVE buttons
        self.status_feedback = QLabel("")
        self.status_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_feedback.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0px;
                min-height: 20px;
            }
        """)
        self.status_feedback.setVisible(False)
        layout.addWidget(self.status_feedback)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Delete Selected button (main action)
        delete_btn = QPushButton("🗑️ Delete Selected Duplicate")
        delete_btn.clicked.connect(self.delete_selected_action)
        delete_btn.setToolTip("Delete the photos that are NOT selected to keep")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                border: 1px solid #f44336;
                font-weight: bold;
                font-size: 13px;
                color: white;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        button_layout.addWidget(delete_btn)
        
        # Copy to Review Album button (NEW FEATURE)
        copy_btn = QPushButton("📋 Copy to Review Album")
        copy_btn.clicked.connect(self.copy_selected_to_review_action)
        copy_btn.setToolTip("Copy all duplicates to a review album for manual deletion later")
        copy_btn.setMinimumHeight(45)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                border: 1px solid #1976D2;
                font-weight: bold;
                font-size: 13px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        button_layout.addWidget(copy_btn)
        
        # Do Nothing button
        do_nothing_btn = QPushButton("🚫 Skip This Group")
        do_nothing_btn.clicked.connect(self.do_nothing)
        do_nothing_btn.setToolTip("Skip this duplicate group - don't delete any copies")
        do_nothing_btn.setMinimumHeight(45)
        do_nothing_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c6c6c;
                border: 1px solid #888888;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #7c7c7c;
            }
            QPushButton:pressed {
                background-color: #8c8c8c;
            }
        """)
        button_layout.addWidget(do_nothing_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def copy_selected_to_review_action(self):
        """Copy duplicates to review album instead of deleting - ENHANCED VERSION"""
        try:
            import credentials
            
            # Get reference to the main window's API
            main_window = self.window()
            if not hasattr(main_window, 'api') or not main_window.api:
                self.show_deletion_feedback("❌ No API connection available", False)
                return
            
            # Initialize enhanced copy operations
            copy_ops = EnhancedPhotoCopyMoveOperations(main_window.api)
            
            # Show processing feedback
            to_copy_count = len(self.duplicates)
            self.show_deletion_feedback(f"🔄 Setting up review album and copying {to_copy_count} photos...", None)
            
            # Process the duplicates
            results = copy_ops.process_duplicates_for_review([self.duplicates], credentials.USER_NAME)
            
            if not results['success']:
                if results.get('manual_creation_needed'):
                    # Show manual creation instructions
                    instructions = results.get('instructions', 'Manual album creation required')
                    album_name = results.get('suggested_album_name', 'MugMatch_Review')
                    
                    feedback_msg = f"📋 Create album manually: {album_name}"
                    self.show_deletion_feedback(feedback_msg, False)
                    
                    # Print detailed instructions to console
                    print(f"\n💡 MANUAL ALBUM CREATION NEEDED:")
                    print(instructions)
                    
                else:
                    error_msg = results.get('error', 'Unknown error occurred')
                    self.show_deletion_feedback(f"❌ Error: {error_msg}", False)
                
                return
            
            # Success - show results
            successful = results['successful_copies']
            failed = results['failed_copies']
            album_info = results['review_album']
            album_name = album_info['album_name']
            
            if successful > 0:
                if failed > 0:
                    success_msg = f"✅ Copied {successful}/{successful + failed} photos to {album_name}"
                else:
                    success_msg = f"✅ All {successful} photos copied to {album_name}!"
                
                self.show_deletion_feedback(success_msg, True)
                
                # Show review album URL if available
                if album_info.get('web_url'):
                    print(f"🌐 Review album: {album_info['web_url']}")
                    
            else:
                # All copies failed - but provide helpful info
                manual_msg = f"📋 Photos need manual copying to {album_name}"
                self.show_deletion_feedback(manual_msg, None)
                
                if album_info.get('web_url'):
                    print(f"💡 Manual review: Visit {album_info['web_url']} and use SmugMug's Collect feature")
            
            # Mark as processed if any copies were successful
            if successful > 0:
                self.mark_as_processed()
                
        except Exception as e:
            error_msg = f"💥 Copy error: {e}"
            self.show_deletion_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    def delete_selected_action(self):
        """Handle the delete selected action - ACTUALLY DELETE FROM SMUGMUG"""
        selected_count = sum(1 for photo in self.duplicates if photo.keep)
        to_delete_count = len(self.duplicates) - selected_count
        
        if selected_count == 0:
            print("Error: No photo selected to keep!")
            self.show_deletion_feedback("❌ Error: No photo selected to keep!", False)
            return
        elif selected_count > 1:
            print("Error: Multiple photos selected to keep!")
            self.show_deletion_feedback("❌ Error: Multiple photos selected to keep!", False)
            return
        
        # Show what will be deleted
        photos_to_delete = [photo for photo in self.duplicates if not photo.keep]
        photos_to_keep = [photo for photo in self.duplicates if photo.keep]
        
        print(f"\n🗑️  ACTUAL DELETION STARTING...")
        print(f"Will delete {to_delete_count} photos, keeping 1")
        
        for photo in photos_to_keep:
            print(f"  ✅ KEEP: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        for photo in photos_to_delete:
            print(f"  🗑️  DELETE: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        # Show processing feedback in GUI
        self.show_deletion_feedback(f"🔄 Deleting {to_delete_count} duplicate photo(s)...", None)
        
        # ACTUAL DELETION - Get API instance
        try:
            import credentials
            from smugmug_api import SmugMugAPIAdapter
            
            api = SmugMugAPIAdapter(
                api_key=credentials.API_KEY,
                api_secret=credentials.API_SECRET,
                access_token=credentials.ACCESS_TOKEN,
                access_secret=credentials.ACCESS_SECRET
            )
            
            # Delete each photo that's not marked to keep
            deletion_results = []
            for photo in photos_to_delete:
                print(f"\n🔄 Deleting {photo.filename} (ID: {photo.image_id})...")
                
                # Try deletion with retry for OAuth nonce conflicts
                success = False
                error_message = ""
                max_retries = 3
                
                for attempt in range(max_retries):
                    if attempt > 0:
                        print(f"Retry attempt {attempt + 1}/{max_retries}")
                        import time
                        time.sleep(2)  # Wait before retry
                    
                    success, error_message = api.delete_image_with_details(photo.image_id)
                    
                    if success:
                        print(f"✅ Successfully deleted {photo.filename}")
                        deletion_results.append((photo, True, None))
                        break
                    elif "nonce" in error_message.lower():
                        print(f"Nonce conflict on attempt {attempt + 1}, retrying...")
                        continue
                    else:
                        print(f"❌ Failed to delete {photo.filename}: {error_message}")
                        deletion_results.append((photo, False, error_message))
                        break
                
                if not success and attempt == max_retries - 1:
                    print(f"❌ Failed to delete {photo.filename} after {max_retries} attempts: {error_message}")
                    deletion_results.append((photo, False, error_message))
            
            # Report final results
            successful_deletions = [r for r in deletion_results if r[1]]
            failed_deletions = [r for r in deletion_results if not r[1]]
            
            print(f"\n📊 DELETION SUMMARY:")
            print(f"✅ Successfully deleted: {len(successful_deletions)} photos")
            print(f"❌ Failed to delete: {len(failed_deletions)} photos")
            
            if failed_deletions:
                print("\n❌ Failed deletions:")
                for photo, _, error in failed_deletions:
                    print(f"   - {photo.filename} (ID: {photo.image_id}): {error}")
                
                # Check for permission issues
                if any("permission" in str(error).lower() or "403" in str(error) for _, _, error in failed_deletions):
                    permission_msg = ("❌ Permission denied. Your SmugMug API application needs 'Modify' permissions. "
                                    "Check your SmugMug API app settings and ensure 'Permissions=Modify' is enabled.")
                    print(f"\n💡 {permission_msg}")
                    self.show_deletion_feedback(permission_msg, False)
                    return
            
            # Mark as processed and show GUI feedback
            if successful_deletions:
                success_msg = f"✅ Successfully deleted {len(successful_deletions)} duplicate photo(s)!"
                print(f"\n{success_msg}")
                self.show_deletion_feedback(success_msg, True)
            else:
                failure_msg = "❌ No photos were deleted. Check console for details."
                if failed_deletions:
                    first_error = failed_deletions[0][2]
                    if "nonce" in str(first_error).lower():
                        failure_msg = "❌ OAuth nonce conflicts persist. SmugMug may be caching nonces server-side."
                    else:
                        failure_msg = f"❌ Deletion failed: {first_error}"
                print(f"\n{failure_msg}")
                self.show_deletion_feedback(failure_msg, False)
                
        except Exception as e:
            error_msg = f"💥 Error during deletion: {e}"
            print(f"\n{error_msg}")
            self.show_deletion_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    def show_deletion_feedback(self, message: str, success: Optional[bool]):
        """Show deletion feedback in the GUI - positioned near buttons"""
        if not hasattr(self, 'status_feedback'):
            return
            
        self.status_feedback.setVisible(True)
        self.status_feedback.setText(message)
        
        if success is None:  # Processing
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #e3f2fd;
                    color: #1565c0;
                    border: 1px solid #2196f3;
                }
            """)
        elif success:  # Success - use green
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #e8f5e8;
                    color: #2e7d32;
                    border: 1px solid #4caf50;
                }
            """)
            # Disable buttons after success
            for button in self.findChildren(QPushButton):
                button.setEnabled(False)
        else:  # Error - use red for attention
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #ffebee;
                    color: #c62828;
                    border: 1px solid #f44336;
                }
            """)
    
    def mark_as_processed(self):
        """Mark this group as processed"""
        # Update header to show it's been processed
        header_widget = self.findChild(QLabel)
        if header_widget and "Duplicate Group" in header_widget.text():
            original_text = header_widget.text()
            header_widget.setText(f"✅ PROCESSED: {original_text}")
            header_widget.setStyleSheet(header_widget.styleSheet().replace(
                'color: #ff6b6b',
                'color: #4CAF50'
            ))
        
        # Disable all buttons in this group
        for button in self.findChildren(QPushButton):
            button.setEnabled(False)
    
    def create_photo_card(self, photo: DuplicatePhoto, index: int) -> QWidget:
        """Create a card widget for a single photo"""
        card = QWidget()
        card.setFixedWidth(320)
        card.setMinimumHeight(480)
        card.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
                border-radius: 8px;
                border: 2px solid #555555;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Radio button for selection
        radio = QRadioButton(f"✓ Keep this copy")
        radio.setChecked(photo.keep)
        radio.toggled.connect(self.on_selection_changed)
        radio.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50;")
        self.button_group.addButton(radio, index)
        self.radio_buttons.append(radio)
        layout.addWidget(radio)
        
        # Photo preview
        preview = PhotoPreviewWidget()
        preview.setMinimumHeight(320)
        preview.setMaximumHeight(350)
        preview.display_photo(photo)
        self.preview_widgets.append(preview)
        layout.addWidget(preview)
        
        # Compact metadata
        metadata_widget = self.create_compact_metadata(photo)
        layout.addWidget(metadata_widget)
        
        layout.addStretch()
        
        return card
    
    def create_compact_metadata(self, photo: DuplicatePhoto) -> QWidget:
        """Create compact metadata display below photo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File info
        size_mb = photo.size / (1024 * 1024) if photo.size > 0 else 0
        
        # Format date
        try:
            if photo.date_uploaded and 'T' in photo.date_uploaded:
                from datetime import datetime
                dt = datetime.fromisoformat(photo.date_uploaded.replace('Z', '+00:00'))
                short_date = dt.strftime("%m/%d/%y")
            else:
                short_date = "Unknown"
        except:
            short_date = "Unknown"
        
        # Compact info lines
        info_lines = [
            f"📁 {photo.album_name[:22]}{'...' if len(photo.album_name) > 22 else ''}",
            f"📄 {photo.filename[:25]}{'...' if len(photo.filename) > 25 else ''}",
            f"📊 {size_mb:.1f} MB  📅 {short_date}"
	    permission_msg = ("❌ Permission denied. Your SmugMug API application needs 'Modify' permissions. "
                                    "Check your SmugMug API app settings and ensure 'Permissions=Modify' is enabled.")
                    print(f"\n💡 {permission_msg}")
                    self.show_deletion_feedback(permission_msg, False)
                    return
            
            # Mark as processed and show GUI feedback
            if successful_deletions:
                success_msg = f"✅ Successfully deleted {len(successful_deletions)} duplicate photo(s)!"
                print(f"\n{success_msg}")
                self.show_deletion_feedback(success_msg, True)
            else:
                failure_msg = "❌ No photos were deleted. Check console for details."
                if failed_deletions:
                    first_error = failed_deletions[0][2]
                    if "nonce" in str(first_error).lower():
                        failure_msg = "❌ OAuth nonce conflicts persist. SmugMug may be caching nonces server-side."
                    else:
                        failure_msg = f"❌ Deletion failed: {first_error}"
                print(f"\n{failure_msg}")
                self.show_deletion_feedback(failure_msg, False)
                
        except Exception as e:
            error_msg = f"💥 Error during deletion: {e}"
            print(f"\n{error_msg}")
            self.show_deletion_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    def show_deletion_feedback(self, message: str, success: Optional[bool]):
        """Show deletion feedback in the GUI - positioned near buttons"""
        if not hasattr(self, 'status_feedback'):
            return
            
        self.status_feedback.setVisible(True)
        self.status_feedback.setText(message)
        
        if success is None:  # Processing
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #e3f2fd;
                    color: #1565c0;
                    border: 1px solid #2196f3;
                }
            """)
        elif success:  # Success - use green
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #e8f5e8;
                    color: #2e7d32;
                    border: 1px solid #4caf50;
                }
            """)
            # Disable buttons after success
            for button in self.findChildren(QPushButton):
                button.setEnabled(False)
        else:  # Error - use red for attention
            self.status_feedback.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0px;
                    min-height: 20px;
                    background-color: #ffebee;
                    color: #c62828;
                    border: 1px solid #f44336;
                }
            """)
    
    def mark_as_processed(self):
        """Mark this group as processed"""
        # Update header to show it's been processed
        header_widget = self.findChild(QLabel)
        if header_widget and "Duplicate Group" in header_widget.text():
            original_text = header_widget.text()
            header_widget.setText(f"✅ PROCESSED: {original_text}")
            header_widget.setStyleSheet(header_widget.styleSheet().replace(
                'color: #ff6b6b',
                'color: #4CAF50'
            ))
        
        # Disable all buttons in this group
        for button in self.findChildren(QPushButton):
            button.setEnabled(False)
    
    def create_photo_card(self, photo: DuplicatePhoto, index: int) -> QWidget:
        """Create a card widget for a single photo"""
        card = QWidget()
        card.setFixedWidth(320)
        card.setMinimumHeight(480)
        card.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
                border-radius: 8px;
                border: 2px solid #555555;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Radio button for selection
        radio = QRadioButton(f"✓ Keep this copy")
        radio.setChecked(photo.keep)
        radio.toggled.connect(self.on_selection_changed)
        radio.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50;")
        self.button_group.addButton(radio, index)
        self.radio_buttons.append(radio)
        layout.addWidget(radio)
        
        # Photo preview
        preview = PhotoPreviewWidget()
        preview.setMinimumHeight(320)
        preview.setMaximumHeight(350)
        preview.display_photo(photo)
        self.preview_widgets.append(preview)
        layout.addWidget(preview)
        
        # Compact metadata
        metadata_widget = self.create_compact_metadata(photo)
        layout.addWidget(metadata_widget)
        
        layout.addStretch()
        
        return card
    
    def create_compact_metadata(self, photo: DuplicatePhoto) -> QWidget:
        """Create compact metadata display below photo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File info
        size_mb = photo.size / (1024 * 1024) if photo.size > 0 else 0
        
        # Format date
        try:
            if photo.date_uploaded and 'T' in photo.date_uploaded:
                from datetime import datetime
                dt = datetime.fromisoformat(photo.date_uploaded.replace('Z', '+00:00'))
                short_date = dt.strftime("%m/%d/%y")
            else:
                short_date = "Unknown"
        except:
            short_date = "Unknown"
        
        # Compact info lines
        info_lines = [
            f"📁 {photo.album_name[:22]}{'...' if len(photo.album_name) > 22 else ''}",
            f"📄 {photo.filename[:25]}{'...' if len(photo.filename) > 25 else ''}",
            f"📊 {size_mb:.1f} MB  📅 {short_date}"
        ]
        
        for line in info_lines:
            label = QLabel(line)
            label.setStyleSheet("""
                font-size: 11px; 
                color: #ffffff; 
                padding: 4px 6px;
                background-color: rgba(60, 60, 60, 0.9);
                border-radius: 4px;
                margin: 1px;
            """)
            label.setWordWrap(True)
            layout.addWidget(label)
        
        return widget
    
    def on_selection_changed(self):
        """Handle radio button selection change"""
        for i, radio in enumerate(self.radio_buttons):
            self.duplicates[i].keep = radio.isChecked()
        self.selection_changed.emit()
    
    def keep_largest_file(self):
        """Select photo with largest file size"""
        if not self.duplicates:
            return
        largest = max(self.duplicates, key=lambda x: x.size or 0)
        self.select_photo(largest)
    
    def keep_oldest_upload(self):
        """Select the oldest uploaded photo"""
        dated_photos = [p for p in self.duplicates if p.date_uploaded]
        if dated_photos:
            oldest = min(dated_photos, key=lambda x: x.date_uploaded)
            self.select_photo(oldest)
        elif self.duplicates:
            self.select_photo(self.duplicates[0])
    
    def keep_newest_upload(self):
        """Select the most recently uploaded photo"""
        dated_photos = [p for p in self.duplicates if p.date_uploaded]
        if dated_photos:
            newest = max(dated_photos, key=lambda x: x.date_uploaded)
            self.select_photo(newest)
        elif self.duplicates:
            self.select_photo(self.duplicates[-1])
    
    def keep_main_album_copy(self):
        """Select the copy in what appears to be the main album"""
        # Simple heuristic: prefer albums with more photos or certain keywords
        main_keywords = ['main', 'primary', 'original', 'master', 'best']
        
        # First try to find an album with main keywords
        for photo in self.duplicates:
            if any(keyword in photo.album_name.lower() for keyword in main_keywords):
                self.select_photo(photo)
                return
        
        # Fallback to first album alphabetically
        sorted_by_album = sorted(self.duplicates, key=lambda x: x.album_name.lower())
        self.select_photo(sorted_by_album[0])
    
    def select_photo(self, photo_to_keep: DuplicatePhoto):
        """Select a specific photo and update UI"""
        for i, photo in enumerate(self.duplicates):
            photo.keep = (photo == photo_to_keep)
            self.radio_buttons[i].setChecked(photo.keep)
        self.selection_changed.emit()
    
    def do_nothing(self):
        """Mark this duplicate group to be skipped"""
        # Uncheck all radio buttons to indicate no action will be taken
        for i, radio in enumerate(self.radio_buttons):
            radio.setChecked(False)
            self.duplicates[i].keep = False
        
        # Update the header to indicate this group is being skipped
        header_widget = self.findChild(QLabel)
        if header_widget and "Duplicate Group" in header_widget.text():
            original_text = header_widget.text()
            header_widget.setText(f"🚫 SKIPPED: {original_text}")
            header_widget.setStyleSheet(header_widget.styleSheet().replace(
                'color: #ff6b6b',
                'color: #888888'
            ))
        
        # Disable all action buttons in this group
        for button in self.findChildren(QPushButton):
            if "Skip" not in button.text():  # Don't disable the skip button itself
                button.setEnabled(False)
        
        self.selection_changed.emit()

class SmugDupsMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api = None
        self.albums = []
        self.duplicate_groups = []
        self.current_group_index = 0
        self.setup_ui()
        QTimer.singleShot(100, self.initialize_app)
        
    def setup_ui(self):
        self.setWindowTitle("SmugDups - SmugMug Duplicate Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Dark theme with better scrollbars
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                border: 1px solid #777777;
            }
            QPushButton:pressed {
                background-color: #5c5c5c;
            }
            QPushButton:disabled {
                background-color: #2c2c2c;
                color: #666666;
                border: 1px solid #444444;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 16px;
                border-radius: 8px;
                border: 1px solid #555555;
            }
            QScrollBar::handle:vertical {
                background-color: #6c6c6c;
                border-radius: 6px;
                margin: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8c8c8c;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #9c9c9c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
            }
            QScrollBar:horizontal {
                background-color: #3c3c3c;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #555555;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c6c6c;
                border-radius: 6px;
                margin: 2px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #8c8c8c;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #9c9c9c;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
            }
            QListWidget {
                background-color: #2e2e2e;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - albums list
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - duplicate results or welcome screen
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([300, 900])
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        load_action = QAction('Load Credentials', self)
        load_action.triggered.connect(self.load_credentials)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Cmd+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        scan_action = QAction('Scan for Duplicates', self)
        scan_action.setShortcut('Cmd+S')
        scan_action.triggered.connect(self.start_duplicate_scan)
        tools_menu.addAction(scan_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About SmugDups', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_control_panel(self) -> QWidget:
        """Create the compact control panel widget"""
        panel = QGroupBox("Controls")
        panel.setMaximumHeight(80)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.refresh_button = QPushButton("🔄 Refresh Albums")
        self.refresh_button.clicked.connect(self.load_albums)
        self.refresh_button.setMinimumHeight(35)
        layout.addWidget(self.refresh_button)
        
        self.scan_button = QPushButton("🔍 Scan for Duplicates")
        self.scan_button.clicked.connect(self.start_duplicate_scan)
        self.scan_button.setMinimumHeight(35)
        self.scan_button.setEnabled(False)
        layout.addWidget(self.scan_button)
        
        # Exit button
        self.exit_button = QPushButton("❌ Exit")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setMinimumHeight(35)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                border: 1px solid #A52A2A;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
            QPushButton:pressed {
                background-color: #B22222;
            }
        """)
        layout.addWidget(self.exit_button)
        
        layout.addStretch()
        
        # Statistics
        self.stats_label = QLabel("Loading albums...")
        self.stats_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        layout.addWidget(self.stats_label)
        
        return panel
    
    def create_left_panel(self) -> QWidget:
        """Create the compact left panel with albums list"""
        panel = QGroupBox("Albums")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # Album selection controls
        controls_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("All")
        self.select_all_btn.clicked.connect(self.select_all_albums)
        self.select_all_btn.setMaximumWidth(50)
        controls_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("None")
        self.select_none_btn.clicked.connect(self.select_no_albums)
        self.select_none_btn.setMaximumWidth(50)
        controls_layout.addWidget(self.select_none_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Sorting controls
        sort_layout = QVBoxLayout()
        
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-top: 5px;")
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "📁 Alphabetical (A-Z)",
            "📁 Alphabetical (Z-A)", 
            "📊 Most Photos First",
            "📊 Fewest Photos First",
            "📅 Newest First",
            "📅 Oldest First"
        ])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 3px;
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAGCAYAAAARx7TFAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABHSURBVAiZY/z//z8DCxYwirkymP3bIc7w/x8D428GBgYGVgYGBgYmBgYGZiYGBgZ2BgYGDgYGBk4GBgYuBgYGbgYGBh4GBgAAWwwJAKvdF7IAAAAASUVORK5CYII=);
                width: 10px;
                height: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                selection-background-color: #4c4c4c;
            }
        """)
        self.sort_combo.currentTextChanged.connect(self.sort_albums)
        sort_layout.addWidget(self.sort_combo)
        
        layout.addLayout(sort_layout)
        
        # Albums list with checkboxes
        self.albums_list = QListWidget()
        self.albums_list.setStyleSheet("""
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #4c4c4c;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
        """)
        layout.addWidget(self.albums_list)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with duplicate groups or welcome message"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create a stacked widget to switch between different views
        self.content_stack = QStackedWidget()
        
        # Welcome screen
        welcome_widget = self.create_welcome_screen()
        self.content_stack.addWidget(welcome_widget)
        
        # Duplicate results screen (scroll area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_stack.addWidget(self.scroll_area)
        
        layout.addWidget(self.content_stack)
        return panel
    
    def create_welcome_screen(self) -> QWidget:
        """Create welcome screen shown before scanning"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome message
        welcome_label = QLabel("🏠 Welcome to SmugDups 2.0")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        instructions = QLabel("""
📋 Instructions:

1. Albums are loading automatically...
2. Select albums from the left panel (or click "All")
3. Click "🔍 Scan for Duplicates" to find duplicate photos
4. Review and manage duplicates when found

💡 New Feature: You can now copy duplicates to a review album
   instead of deleting them immediately!

🔍 Tip: Start with smaller albums first to test the process!
        """)
        instructions.setStyleSheet("font-size: 14px; line-height: 1.5; color: #cccccc; max-width: 400px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        layout.addStretch()
        return widget
    
    def initialize_app(self):
        """Initialize the application by loading credentials and albums"""
        self.load_credentials()
        if self.api:
            self.load_albums()
    
    def load_credentials(self):
        """Load SmugMug API credentials"""
        try:
            import credentials
            from smugmug_api import SmugMugAPIAdapter
            
            self.api = SmugMugAPIAdapter(
                api_key=credentials.API_KEY,
                api_secret=credentials.API_SECRET,
                access_token=credentials.ACCESS_TOKEN,
                access_secret=credentials.ACCESS_SECRET
            )
            
            # Test the connection
            print("Testing SmugMug API connection...")
            user_info = self.api.get_user_info(credentials.USER_NAME)
            if user_info:
                self.status_bar.showMessage(f"Connected as {user_info.get('Name', credentials.USER_NAME)}")
                print(f"Successfully connected to SmugMug as: {user_info.get('Name', credentials.USER_NAME)}")
            else:
                self.status_bar.showMessage("API connection test failed")
                print("API connection test failed")
                
        except ImportError as e:
            self.status_bar.showMessage("credentials.py file not found")
            print(f"Could not import credentials.py: {e}")
            self.api = None
        except AttributeError as e:
            self.status_bar.showMessage("Missing credentials in credentials.py")
            print(f"Missing required credentials: {e}")
            self.api = None
        except Exception as e:
            self.status_bar.showMessage(f"Failed to load credentials: {e}")
            print(f"Credential loading error: {e}")
            self.api = None

    def load_albums(self):
        """Load albums from SmugMug"""
        if not self.api:
            self.status_bar.showMessage("No API connection - please check credentials")
            return
        
        self.status_bar.showMessage("Loading albums...")
        self.refresh_button.setEnabled(False)
        self.stats_label.setText("Loading albums...")
        
        # Start background thread to load albums
        class AlbumLoader(QThread):
            albums_loaded = pyqtSignal(list)
            error_occurred = pyqtSignal(str)
            
            def __init__(self, api, user_name):
                super().__init__()
                self.api = api
                self.user_name = user_name
                
            def run(self):
                try:
                    print(f"Loading albums for user: {self.user_name}")
                    albums = self.api.get_user_albums(self.user_name)
                    print(f"Loaded {len(albums)} albums")
                    self.albums_loaded.emit(albums)
                except Exception as e:
                    print(f"Error loading albums: {e}")
                    self.error_occurred.emit(str(e))
        
        # Load credentials to get username
        try:
            import credentials
            user_name = credentials.USER_NAME
            
            self.album_loader = AlbumLoader(self.api, user_name)
            self.album_loader.albums_loaded.connect(self.on_albums_loaded)
            self.album_loader.error_occurred.connect(self.on_albums_error)
            self.album_loader.start()
            
        except Exception as e:
            self.on_albums_error(f"Failed to load credentials: {e}")
    
    def on_albums_loaded(self, albums):
        """Handle successful album loading"""
        self.albums = albums
        
        # Add creation date to albums (extracted from date patterns in album names or use current date as fallback)
        for album in self.albums:
            # Try to extract date from album name or use a default
            album['sort_date'] = self.extract_album_date(album.get('name', ''))
        
        # Sort albums alphabetically by default to match the dropdown default
        self.albums.sort(key=lambda x: x['name'].lower())
        
        self.populate_albums_list()
        self.refresh_button.setEnabled(True)
        self.scan_button.setEnabled(True)
        self.status_bar.showMessage(f"Loaded {len(albums)} albums")
        self.stats_label.setText(f"{len(albums)} albums loaded")
        
        print(f"Successfully loaded {len(albums)} albums")
        for i, album in enumerate(albums[:5]):
            print(f"  {i+1}. {album['name']} ({album['image_count']} images)")
    
    def extract_album_date(self, album_name: str) -> str:
        """Extract or estimate date from album name for sorting"""
        import re
        from datetime import datetime
        
        # Try to find year patterns in album name
        year_patterns = [
            r'(\d{4})',  # Any 4-digit year
            r'(19\d{2}|20\d{2})',  # Specific year ranges
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, album_name)
            if match:
                year = int(match.group(1))
                # Create a date string for this year (use mid-year as default)
                return f"{year}-06-15"
        
        # Check for month/year patterns
        month_year_patterns = [
            r'(\d{1,2})/(\d{4})',  # MM/YYYY
            r'(\d{4})-(\d{1,2})',  # YYYY-MM
        ]
        
        for pattern in month_year_patterns:
            match = re.search(pattern, album_name)
            if match:
                if len(match.group(1)) == 4:  # YYYY-MM format
                    year, month = match.groups()
                else:
else:  # MM/YYYY format
                   month, year = match.groups()
               return f"{year}-{int(month):02d}-15"
       
       # Special album name patterns
       if any(word in album_name.lower() for word in ['christmas', 'xmas']):
           # Extract year if present, otherwise use 2000
           year_match = re.search(r'(\d{4})', album_name)
           year = year_match.group(1) if year_match else '2000'
           return f"{year}-12-25"
       
       if any(word in album_name.lower() for word in ['wedding', 'graduation']):
           year_match = re.search(r'(\d{4})', album_name)
           year = year_match.group(1) if year_match else '2000'
           return f"{year}-06-15"
       
       # Default to a very old date for albums without recognizable dates
       return "1900-01-01"
   
   def sort_albums(self):
       """Sort albums based on selected criteria"""
       if not self.albums:
           return
       
       sort_option = self.sort_combo.currentText()
       
       if "Alphabetical (A-Z)" in sort_option:
           self.albums.sort(key=lambda x: x['name'].lower())
       elif "Alphabetical (Z-A)" in sort_option:
           self.albums.sort(key=lambda x: x['name'].lower(), reverse=True)
       elif "Most Photos First" in sort_option:
           self.albums.sort(key=lambda x: x.get('image_count', 0), reverse=True)
       elif "Fewest Photos First" in sort_option:
           self.albums.sort(key=lambda x: x.get('image_count', 0))
       elif "Newest First" in sort_option:
           self.albums.sort(key=lambda x: x.get('sort_date', '1900-01-01'), reverse=True)
       elif "Oldest First" in sort_option:
           self.albums.sort(key=lambda x: x.get('sort_date', '1900-01-01'))
       
       # Remember selected albums before repopulating
       selected_album_ids = self.get_selected_albums()
       
       # Repopulate the list
       self.populate_albums_list()
       
       # Restore selections
       self.restore_album_selections(selected_album_ids)
       
       print(f"Albums sorted by: {sort_option}")
   
   def restore_album_selections(self, selected_album_ids: List[str]):
       """Restore album selections after sorting"""
       if not selected_album_ids:
           return
       
       for i in range(self.albums_list.count()):
           item = self.albums_list.item(i)
           album_id = item.data(Qt.ItemDataRole.UserRole)
           if album_id in selected_album_ids:
               item.setCheckState(Qt.CheckState.Checked)
   
   def on_albums_error(self, error_message):
       """Handle album loading errors"""
       self.refresh_button.setEnabled(True)
       self.status_bar.showMessage(f"Failed to load albums: {error_message}")
       self.stats_label.setText("Album loading failed")
       print(f"Album loading error: {error_message}")
   
   def populate_albums_list(self):
       """Populate the albums list widget with enhanced information"""
       self.albums_list.clear()
       
       print(f"Populating album list with {len(self.albums)} albums")
       
       for i, album in enumerate(self.albums):
           try:
               album_name = album.get('name', f'Album {i}')
               image_count = album.get('image_count', 0)
               album_id = album.get('id', f'unknown_{i}')
               
               print(f"Creating item {i}: '{album_name}' ({image_count} images) ID: {album_id}")
               
               # Create a simple list item with text
               display_text = f"{album_name} ({image_count})"
               
               # Add year if available
               sort_date = album.get('sort_date', '')
               if sort_date and sort_date != '1900-01-01':
                   year = sort_date.split('-')[0]
                   if year != '1900':
                       display_text += f" ~{year}"
               
               # Create the list item
               item = QListWidgetItem(display_text)
               
               # Store album data in the item
               item.setData(Qt.ItemDataRole.UserRole, album_id)
               
               # Set checkable
               item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
               item.setCheckState(Qt.CheckState.Unchecked)
               
               # Color code by image count
               if image_count == 0:
                   item.setForeground(QColor(136, 136, 136))  # Gray for empty
               elif image_count < 10:
                   item.setForeground(QColor(204, 204, 204))  # Light gray for few
               elif image_count < 100:
                   item.setForeground(QColor(255, 255, 255))  # White for normal
               else:
                   item.setForeground(QColor(76, 175, 80))   # Green for many
               
               # Add to list
               self.albums_list.addItem(item)
               
               print(f"Successfully added item {i}")
               
           except Exception as e:
               print(f"Error creating album list item {i} for album {album.get('name', 'Unknown')}: {e}")
               # Create a simple fallback item
               try:
                   fallback_text = f"Error: {album.get('name', f'Album {i}')}"
                   fallback_item = QListWidgetItem(fallback_text)
                   fallback_item.setData(Qt.ItemDataRole.UserRole, album.get('id', f'error_{i}'))
                   fallback_item.setFlags(fallback_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                   fallback_item.setCheckState(Qt.CheckState.Unchecked)
                   fallback_item.setForeground(QColor(255, 100, 100))  # Red for errors
                   self.albums_list.addItem(fallback_item)
                   print(f"Added fallback item for album {i}")
               except Exception as e2:
                   print(f"Failed to create fallback item: {e2}")
       
       print(f"Album list population complete. Total items: {self.albums_list.count()}")
   
   def select_all_albums(self):
       """Select all albums"""
       for i in range(self.albums_list.count()):
           item = self.albums_list.item(i)
           if item:
               item.setCheckState(Qt.CheckState.Checked)
   
   def select_no_albums(self):
       """Deselect all albums"""
       for i in range(self.albums_list.count()):
           item = self.albums_list.item(i)
           if item:
               item.setCheckState(Qt.CheckState.Unchecked)
   
   def get_selected_albums(self):
       """Get list of selected album IDs"""
       selected = []
       print(f"Checking {self.albums_list.count()} albums for selections...")
       
       for i in range(self.albums_list.count()):
           item = self.albums_list.item(i)
           if item and item.checkState() == Qt.CheckState.Checked:
               album_id = item.data(Qt.ItemDataRole.UserRole)
               if album_id:
                   selected.append(album_id)
                   print(f"Selected album: {item.text()} (ID: {album_id})")
       
       print(f"Total selected albums: {len(selected)}")
       return selected

   def start_duplicate_scan(self):
       """Start scanning selected albums for duplicates"""
       selected_albums = self.get_selected_albums()
       
       if not selected_albums:
           self.status_bar.showMessage("Please select at least one album to scan")
           return
       
       print(f"Starting duplicate scan of {len(selected_albums)} selected albums")
       
       # Start background scanning
       self.progress_bar.setVisible(True)
       self.scan_button.setEnabled(False)
       self.refresh_button.setEnabled(False)
       
       self.finder_thread = DuplicateFinderThread(self.api, selected_albums)
       self.finder_thread.progress_updated.connect(self.update_progress)
       self.finder_thread.duplicates_found.connect(self.display_duplicates)
       self.finder_thread.finished.connect(self.scan_finished)
       self.finder_thread.error_occurred.connect(self.handle_error)
       self.finder_thread.start()
   
   def update_progress(self, value: int, message: str):
       """Update progress bar and status"""
       self.progress_bar.setValue(value)
       self.status_bar.showMessage(message)
   
   def display_duplicates(self, duplicate_groups: List[List[DuplicatePhoto]]):
       """Display found duplicate groups"""
       self.duplicate_groups = duplicate_groups
       
       if not duplicate_groups:
           # Show "no duplicates found" message
           no_dupes_widget = QWidget()
           layout = QVBoxLayout(no_dupes_widget)
           layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
           
           message = QLabel("🎉 No Duplicates Found!")
           message.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50; margin: 20px;")
           message.setAlignment(Qt.AlignmentFlag.AlignCenter)
           layout.addWidget(message)
           
           submessage = QLabel("Your selected albums are duplicate-free!")
           submessage.setStyleSheet("font-size: 16px; color: #cccccc;")
           submessage.setAlignment(Qt.AlignmentFlag.AlignCenter)
           layout.addWidget(submessage)
           
           self.scroll_area.setWidget(no_dupes_widget)
       else:
           # Create container for duplicate groups
           container = QWidget()
           container_layout = QVBoxLayout(container)
           
           # Add header with summary
           total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
           total_waste = sum(sum(photo.size for photo in group[1:]) for group in duplicate_groups)
           waste_mb = total_waste / (1024 * 1024)
           
           header = QLabel(f"🔍 Found {len(duplicate_groups)} duplicate groups ({total_duplicates} duplicates wasting {waste_mb:.1f} MB)")
           header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff6b6b; margin: 10px; padding: 10px; background-color: #3c3c3c; border-radius: 5px;")
           container_layout.addWidget(header)
           
           # Add instruction text
           instruction = QLabel("👆 Review each group below. Use the radio buttons to select which copy to KEEP, then choose an action.")
           instruction.setStyleSheet("font-size: 14px; color: #cccccc; margin: 5px 10px; padding: 8px; background-color: #2e2e2e; border-radius: 3px;")
           container_layout.addWidget(instruction)
           
           # Add feature highlight
           feature_highlight = QLabel("✨ NEW: You can now copy duplicates to a review album for manual deletion later!")
           feature_highlight.setStyleSheet("font-size: 13px; color: #2196F3; margin: 5px 10px; padding: 6px; background-color: #1a237e; border-radius: 3px; border: 1px solid #2196F3;")
           container_layout.addWidget(feature_highlight)
           
           # Add each duplicate group
           for i, group in enumerate(duplicate_groups):
               group_widget = DuplicateGroupWidget(group)
               group_widget.selection_changed.connect(self.on_selection_changed)
               
               # Add separator between groups
               if i > 0:
                   separator = QLabel("")
                   separator.setStyleSheet("border-top: 2px solid #555555; margin: 10px 0;")
                   separator.setMaximumHeight(2)
                   container_layout.addWidget(separator)
               
               container_layout.addWidget(group_widget)
           
           container_layout.addStretch()
           self.scroll_area.setWidget(container)
       
       # Switch to results view
       self.content_stack.setCurrentIndex(1)
       
       # Update statistics
       if duplicate_groups:
           total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
           self.stats_label.setText(f"{len(duplicate_groups)} groups, {total_duplicates} duplicates found")
       else:
           self.stats_label.setText("No duplicates found")
   
   def on_selection_changed(self):
       """Handle changes in duplicate selection"""
       pass
   
   def scan_finished(self):
       """Handle scan completion"""
       self.progress_bar.setVisible(False)
       self.scan_button.setEnabled(True)
       self.refresh_button.setEnabled(True)
       self.status_bar.showMessage("Scan completed")
   
   def handle_error(self, error_message: str):
       """Handle errors during scanning"""
       self.progress_bar.setVisible(False)
       self.scan_button.setEnabled(True)
       self.status_bar.showMessage(f"Error: {error_message}")
       print(f"Scan error: {error_message}")

   def show_about(self):
       """Show about dialog"""
       from PyQt6.QtWidgets import QMessageBox
       
       about_text = """
<h2>SmugDups 2.0</h2>
<p><b>Modern SmugMug Duplicate Photo Manager</b></p>
<p>A modernized version of the original SmugDups tool for finding and managing duplicate photos in your SmugMug account.</p>

<h3>Features:</h3>
<ul>
<li>✓ Scan specific albums or entire account</li>
<li>✓ Advanced duplicate detection using MD5 hashes</li>
<li>✓ Smart selection recommendations</li>
<li>✓ Modern PyQt6 interface for macOS</li>
<li>✓ Background processing with progress tracking</li>
<li>✓ Real photo thumbnails with caching</li>
<li>✓ <b>NEW:</b> Copy duplicates to review album option</li>
<li>✓ Enhanced duplicate management workflow</li>
</ul>

<h3>New in Version 2.0:</h3>
<ul>
<li>🆕 Copy to Review Album feature</li>
<li>🆕 Non-destructive duplicate management</li>
<li>🆕 Automatic review album creation</li>
<li>🆕 Enhanced error handling</li>
</ul>

<h3>Credits:</h3>
<p>Based on the original SmugDups by AndrewsOR<br>
Modernized interface and SmugMug API v2 integration<br>
Enhanced copy functionality integration</p>

<p><i>Version 2.0 - 2025</i></p>
       """
       
       msg = QMessageBox()
       msg.setWindowTitle("About SmugDups")
       msg.setTextFormat(Qt.TextFormat.RichText)
       msg.setText(about_text)
       msg.setStyleSheet("""
           QMessageBox {
               background-color: #2b2b2b;
               color: #ffffff;
           }
           QMessageBox QPushButton {
               background-color: #3c3c3c;
               border: 1px solid #555555;
               padding: 8px 16px;
               border-radius: 4px;
               min-width: 80px;
           }
           QMessageBox QPushButton:hover {
               background-color: #4c4c4c;
           }
       """)
       msg.exec()
   
   def closeEvent(self, event):
       """Handle application closing"""
       if hasattr(self, 'finder_thread') and self.finder_thread.isRunning():
           from PyQt6.QtWidgets import QMessageBox
           
           reply = QMessageBox.question(
               self, 
               'Exit SmugDups', 
               'A scan is currently in progress. Are you sure you want to exit?',
               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
               QMessageBox.StandardButton.No
           )
           
           if reply == QMessageBox.StandardButton.Yes:
               self.finder_thread.terminate()
               self.finder_thread.wait()
               event.accept()
           else:
               event.ignore()
       else:
           event.accept()

def main():
   """Main application entry point"""
   app = QApplication(sys.argv)
   
   # Set application properties
   app.setApplicationName("SmugDups")
   app.setApplicationVersion("2.0")
   app.setOrganizationName("SmugDups")
   
   # Create and show main window
   window = SmugDupsMainWindow()
   window.show()
   
   sys.exit(app.exec())

if __name__ == "__main__":
   main()
