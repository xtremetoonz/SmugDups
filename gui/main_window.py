"""
Main application window for SmugDups v5.1
File: gui/main_window.py
UPDATED: v5.1 with GPS coordinate support and enhanced UI messaging
"""

from typing import List
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
    QLabel, QListWidget, QListWidgetItem, QSplitter, QGroupBox, 
    QProgressBar, QStatusBar, QComboBox, QStackedWidget, QScrollArea,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor
from core.duplicate_finder import DuplicateFinderThread
from core.models import DuplicatePhoto
from gui.duplicate_widget import DuplicateGroupWidget

class AlbumLoader(QThread):
    """Background thread for loading albums"""
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

class SmugDupsMainWindow(QMainWindow):
    """Main application window for SmugDups v5.1 with GPS support"""
    
    def __init__(self):
        super().__init__()
        self.api = None
        self.albums = []
        self.duplicate_groups = []
        self._setup_ui()
        QTimer.singleShot(100, self._initialize_app)
        
    def _setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("SmugDups - SmugMug Duplicate Photo Manager v5.1")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add components
        main_layout.addWidget(self._create_control_panel())
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.addWidget(self._create_left_panel())
        content_splitter.addWidget(self._create_right_panel())
        content_splitter.setSizes([300, 900])
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("SmugDups v5.1 Ready - Now with GPS coordinate support!")
    
    def _apply_dark_theme(self):
        """Apply dark theme styling"""
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
            QListWidget {
                background-color: #2e2e2e;
                border: 1px solid #555555;
                border-radius: 4px;
            }
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
            QComboBox {
                font-size: 10px;
                padding: 3px;
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                selection-background-color: #4c4c4c;
            }
        """)
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        load_action = QAction('Load Credentials', self)
        load_action.triggered.connect(self._load_credentials)
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
        scan_action.triggered.connect(self._start_duplicate_scan)
        tools_menu.addAction(scan_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About SmugDups', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel"""
        panel = QGroupBox("Controls")
        panel.setMaximumHeight(80)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.refresh_button = QPushButton("🔄 Refresh Albums")
        self.refresh_button.clicked.connect(self._load_albums)
        self.refresh_button.setMinimumHeight(35)
        layout.addWidget(self.refresh_button)
        
        self.scan_button = QPushButton("🔍 Scan for Duplicates")
        self.scan_button.clicked.connect(self._start_duplicate_scan)
        self.scan_button.setMinimumHeight(35)
        self.scan_button.setEnabled(False)
        layout.addWidget(self.scan_button)
        
        exit_button = QPushButton("❌ Exit")
        exit_button.clicked.connect(self.close)
        exit_button.setMinimumHeight(35)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                border: 1px solid #A52A2A;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
        """)
        layout.addWidget(exit_button)
        
        layout.addStretch()
        
        self.stats_label = QLabel("Loading albums...")
        self.stats_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        layout.addWidget(self.stats_label)
        
        return panel
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with albums list"""
        panel = QGroupBox("Albums")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # Album selection controls
        controls_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("All")
        select_all_btn.clicked.connect(self._select_all_albums)
        select_all_btn.setMaximumWidth(50)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("None")
        select_none_btn.clicked.connect(self._select_no_albums)
        select_none_btn.setMaximumWidth(50)
        controls_layout.addWidget(select_none_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Sorting controls
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-top: 5px;")
        layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "📁 Alphabetical (A-Z)",
            "📁 Alphabetical (Z-A)", 
            "📊 Most Photos First",
            "📊 Fewest Photos First",
            "📅 Newest First",
            "📅 Oldest First"
        ])
        self.sort_combo.currentTextChanged.connect(self._sort_albums)
        layout.addWidget(self.sort_combo)
        
        # Albums list
        self.albums_list = QListWidget()
        layout.addWidget(self.albums_list)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with content stack"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.content_stack = QStackedWidget()
        
        # Welcome screen
        welcome_widget = self._create_welcome_screen()
        self.content_stack.addWidget(welcome_widget)
        
        # Results screen
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_stack.addWidget(self.scroll_area)
        
        layout.addWidget(self.content_stack)
        return panel
    
    def _create_welcome_screen(self) -> QWidget:
        """Create welcome screen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_label = QLabel("🏠 Welcome to SmugDups v5.1")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        instructions = QLabel("""
📋 Instructions:

1. Albums are loading automatically...
2. Select albums from the left panel (or click "All")
3. Click "🔍 Scan for Duplicates" to find duplicate photos
4. Review and manage duplicates when found

🎉 NEW in v5.1: GPS Coordinate Support!
   🗺️ Displays latitude, longitude, and altitude when available
   📍 Location-aware quality scoring for better duplicate selection
   🌍 Enhanced metadata with geographic context
   📊 Group statistics show GPS data availability

✅ All v5.0 Features Preserved:
   ✅ WORKING moveimages functionality - true moves!
   ✅ No manual cleanup needed - fully automated!
   ✅ SmugMug API v2 compliant with proper parameters

🔍 Tip: Start with smaller albums first to test the process!
Perfect for travel photographers who geotag their work!
        """)
        instructions.setStyleSheet("font-size: 14px; line-height: 1.5; color: #cccccc; max-width: 500px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        layout.addStretch()
        return widget
    
    def _initialize_app(self):
        """Initialize the application"""
        self._load_credentials()
        if self.api:
            self._load_albums()
    
    def _load_credentials(self):
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
                self.status_bar.showMessage(f"SmugDups v5.1 - Connected as {user_info.get('Name', credentials.USER_NAME)} (GPS support enabled)")
                print(f"Successfully connected to SmugMug as: {user_info.get('Name', credentials.USER_NAME)}")
            else:
                self.status_bar.showMessage("SmugDups v5.1 - API connection test failed")
                print("API connection test failed")
                
        except ImportError as e:
            self.status_bar.showMessage("SmugDups v5.1 - credentials.py file not found")
            print(f"Could not import credentials.py: {e}")
            self.api = None
        except Exception as e:
            self.status_bar.showMessage(f"SmugDups v5.1 - Failed to load credentials: {e}")
            print(f"Credential loading error: {e}")
            self.api = None

    def _load_albums(self):
        """Load albums from SmugMug"""
        if not self.api:
            self.status_bar.showMessage("SmugDups v5.1 - No API connection - please check credentials")
            return
        
        self.status_bar.showMessage("SmugDups v5.1 - Loading albums...")
        self.refresh_button.setEnabled(False)
        self.stats_label.setText("Loading albums...")
        
        try:
            import credentials
            user_name = credentials.USER_NAME
            
            self.album_loader = AlbumLoader(self.api, user_name)
            self.album_loader.albums_loaded.connect(self._on_albums_loaded)
            self.album_loader.error_occurred.connect(self._on_albums_error)
            self.album_loader.start()
            
        except Exception as e:
            self._on_albums_error(f"Failed to load credentials: {e}")
    
    def _on_albums_loaded(self, albums):
        """Handle successful album loading"""
        self.albums = albums
        
        # Add sort dates for albums
        for album in self.albums:
            album['sort_date'] = self._extract_album_date(album.get('name', ''))
        
        # Sort alphabetically by default
        self.albums.sort(key=lambda x: x['name'].lower())
        
        self._populate_albums_list()
        self.refresh_button.setEnabled(True)
        self.scan_button.setEnabled(True)
        self.status_bar.showMessage(f"SmugDups v5.1 - Loaded {len(albums)} albums (GPS support ready)")
        self.stats_label.setText(f"{len(albums)} albums loaded")
        
        print(f"Successfully loaded {len(albums)} albums")
    
    def _on_albums_error(self, error_message):
        """Handle album loading errors"""
        self.refresh_button.setEnabled(True)
        self.status_bar.showMessage(f"SmugDups v5.1 - Failed to load albums: {error_message}")
        self.stats_label.setText("Album loading failed")
        print(f"Album loading error: {error_message}")
    
    def _extract_album_date(self, album_name: str) -> str:
        """Extract date from album name for sorting"""
        import re
        
        # Try to find year patterns
        year_patterns = [r'(\d{4})', r'(19\d{2}|20\d{2})']
        
        for pattern in year_patterns:
            match = re.search(pattern, album_name)
            if match:
                year = int(match.group(1))
                return f"{year}-06-15"
        
        # Default for albums without dates
        return "1900-01-01"
    
    def _populate_albums_list(self):
        """Populate the albums list widget"""
        self.albums_list.clear()
        
        for i, album in enumerate(self.albums):
            try:
                album_name = album.get('name', f'Album {i}')
                image_count = album.get('image_count', 0)
                album_id = album.get('id', f'unknown_{i}')
                
                display_text = f"{album_name} ({image_count})"
                
                # Add year if available
                sort_date = album.get('sort_date', '')
                if sort_date and sort_date != '1900-01-01':
                    year = sort_date.split('-')[0]
                    if year != '1900':
                        display_text += f" ~{year}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, album_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                
                # Color code by image count
                if image_count == 0:
                    item.setForeground(QColor(136, 136, 136))
                elif image_count < 10:
                    item.setForeground(QColor(204, 204, 204))
                elif image_count < 100:
                    item.setForeground(QColor(255, 255, 255))
                else:
                    item.setForeground(QColor(76, 175, 80))
                
                self.albums_list.addItem(item)
                
            except Exception as e:
                print(f"Error creating album list item: {e}")
    
    def _sort_albums(self):
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
        
        selected_album_ids = self._get_selected_albums()
        self._populate_albums_list()
        self._restore_album_selections(selected_album_ids)
    
    def _select_all_albums(self):
        """Select all albums"""
        for i in range(self.albums_list.count()):
            item = self.albums_list.item(i)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def _select_no_albums(self):
        """Deselect all albums"""
        for i in range(self.albums_list.count()):
            item = self.albums_list.item(i)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def _get_selected_albums(self) -> List[str]:
        """Get list of selected album IDs"""
        selected = []
        for i in range(self.albums_list.count()):
            item = self.albums_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                album_id = item.data(Qt.ItemDataRole.UserRole)
                if album_id:
                    selected.append(album_id)
        return selected
    
    def _restore_album_selections(self, selected_album_ids: List[str]):
        """Restore album selections after sorting"""
        if not selected_album_ids:
            return
        
        for i in range(self.albums_list.count()):
            item = self.albums_list.item(i)
            album_id = item.data(Qt.ItemDataRole.UserRole)
            if album_id in selected_album_ids:
                item.setCheckState(Qt.CheckState.Checked)

    def _start_duplicate_scan(self):
        """Start scanning selected albums for duplicates"""
        selected_albums = self._get_selected_albums()
        
        if not selected_albums:
            self.status_bar.showMessage("SmugDups v5.1 - Please select at least one album to scan")
            return
        
        print(f"Starting duplicate scan of {len(selected_albums)} selected albums with GPS support")
        
        self.progress_bar.setVisible(True)
        self.scan_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        self.finder_thread = DuplicateFinderThread(self.api, selected_albums)
        self.finder_thread.progress_updated.connect(self._update_progress)
        self.finder_thread.duplicates_found.connect(self._display_duplicates)
        self.finder_thread.finished.connect(self._scan_finished)
        self.finder_thread.error_occurred.connect(self._handle_error)
        self.finder_thread.start()
    
    def _update_progress(self, value: int, message: str):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(f"SmugDups v5.1 - {message}")
    
    def _display_duplicates(self, duplicate_groups: List[List[DuplicatePhoto]]):
        """Display found duplicate groups"""
        self.duplicate_groups = duplicate_groups
        
        if not duplicate_groups:
            self._show_no_duplicates_screen()
        else:
            self._show_duplicates_screen(duplicate_groups)
        
        # Switch to results view
        self.content_stack.setCurrentIndex(1)
        
        # Update statistics with GPS info
        if duplicate_groups:
            total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
            total_with_gps = sum(1 for group in duplicate_groups for photo in group if photo.has_location())
            if total_with_gps > 0:
                self.stats_label.setText(f"{len(duplicate_groups)} groups, {total_duplicates} duplicates found ({total_with_gps} with GPS)")
            else:
                self.stats_label.setText(f"{len(duplicate_groups)} groups, {total_duplicates} duplicates found")
        else:
            self.stats_label.setText("No duplicates found")
    
    def _show_no_duplicates_screen(self):
        """Show no duplicates found message"""
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
    
    def _show_duplicates_screen(self, duplicate_groups: List[List[DuplicatePhoto]]):
        """Show duplicates found screen"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Add header with summary including GPS stats
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
        total_waste = sum(sum(photo.size for photo in group[1:]) for group in duplicate_groups)
        waste_mb = total_waste / (1024 * 1024)
        total_with_gps = sum(1 for group in duplicate_groups for photo in group if photo.has_location())
        
        gps_text = f" • {total_with_gps} photos with GPS data" if total_with_gps > 0 else ""
        
        header = QLabel(f"🔍 Found {len(duplicate_groups)} duplicate groups ({total_duplicates} duplicates wasting {waste_mb:.1f} MB{gps_text})")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff6b6b; margin: 10px; padding: 10px; background-color: #3c3c3c; border-radius: 5px;")
        container_layout.addWidget(header)
        
        # Add instruction text
        instruction = QLabel("👆 Review each group below. Use the radio buttons to select which copy to KEEP, then choose an action.")
        instruction.setStyleSheet("font-size: 14px; color: #cccccc; margin: 5px 10px; padding: 8px; background-color: #2e2e2e; border-radius: 3px;")
        container_layout.addWidget(instruction)
        
        # Add feature highlight
        feature_highlight = QLabel("🎉 SmugDups v5.1: GPS coordinate support + working moveimages - True moves with no manual cleanup needed!")
        feature_highlight.setStyleSheet("font-size: 13px; color: #4CAF50; margin: 5px 10px; padding: 6px; background-color: #1b5e20; border-radius: 3px; border: 1px solid #4CAF50;")
        container_layout.addWidget(feature_highlight)
        
        # Add each duplicate group
        for i, group in enumerate(duplicate_groups):
            group_widget = DuplicateGroupWidget(group)
            group_widget.selection_changed.connect(self._on_selection_changed)
            
            # Add separator between groups
            if i > 0:
                separator = QLabel("")
                separator.setStyleSheet("border-top: 2px solid #555555; margin: 10px 0;")
                separator.setMaximumHeight(2)
                container_layout.addWidget(separator)
            
            container_layout.addWidget(group_widget)
        
        container_layout.addStretch()
        self.scroll_area.setWidget(container)
    
    def _on_selection_changed(self):
        """Handle changes in duplicate selection"""
        pass
    
    def _scan_finished(self):
        """Handle scan completion"""
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.status_bar.showMessage("SmugDups v5.1 - Scan completed")
    
    def _handle_error(self, error_message: str):
        """Handle errors during scanning"""
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.status_bar.showMessage(f"SmugDups v5.1 - Error: {error_message}")
        print(f"Scan error: {error_message}")

    def _show_about(self):
        """Show about dialog"""
        about_text = """
<h2>SmugDups v5.1</h2>
        <p><i>Version 5.1 - 2025</i></p>
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
            event.accept()<b>SmugMug Duplicate Photo Manager</b></p>
<p>Advanced duplicate photo detection and management for SmugMug accounts with working moveimages functionality and GPS coordinate support.</p>

<h3>New in Version 5.1:</h3>
<ul>
<li>🗺️ GPS coordinate support (latitude, longitude, altitude)</li>
<li>📍 Location-aware quality scoring for better duplicate selection</li>
<li>🌍 Enhanced metadata with geographic context</li>
<li>📊 Group statistics show GPS data availability</li>
<li>🔄 Distance calculations between geotagged duplicates</li>
</ul>

<h3>Features from v5.0:</h3>
<ul>
<li>🎉 WORKING moveimages functionality</li>
<li>✅ True moves - duplicates removed from source albums</li>
<li>✅ No manual cleanup needed - fully automated</li>
<li>✅ SmugMug API v2 compliant with proper parameters</li>
<li>🔄 Enhanced error handling and verification</li>
</ul>

<h3>Core Features:</h3>
<ul>
<li>MD5-based duplicate detection across albums</li>
<li>PyQt6 modern GUI interface</li>
<li>Automatic review album creation</li>
<li>OAuth1 authentication with redirect handling</li>
<li>Comprehensive duplicate management workflow</li>
</ul>

<p
