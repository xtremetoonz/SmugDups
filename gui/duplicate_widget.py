"""
Widget to display and manage a group of duplicate photos for SmugDups v5.1
File: gui/duplicate_widget.py
FIXED: Radio button selection now works properly
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QRadioButton, QButtonGroup, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt

from core.models import DuplicatePhoto
from .photo_preview import PhotoPreviewWidget

class DuplicateGroupWidget(QWidget):
    """Widget to display and manage a group of duplicate photos - SmugDups v5.1 FIXED"""
    
    selection_changed = pyqtSignal()
    
    def __init__(self, duplicates: List[DuplicatePhoto]):
        super().__init__()
        self.duplicates = duplicates
        self.radio_buttons = []
        self.button_group = QButtonGroup()
        self.preview_widgets = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Group header
        header = self._create_header()
        layout.addWidget(header)
        
        # Photos in horizontal scroll area
        scroll_area = self._create_photos_scroll_area()
        layout.addWidget(scroll_area)
        
        # Status feedback area
        self.status_feedback = self._create_status_feedback()
        layout.addWidget(self.status_feedback)
        
        # Action buttons
        button_layout = self._create_action_buttons()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_header(self) -> QLabel:
        """Create group header with summary information"""
        # Calculate group statistics
        waste_size = sum(photo.size for photo in self.duplicates[1:])
        waste_mb = waste_size / (1024*1024)
        quality_scores = [photo.get_quality_score() for photo in self.duplicates]
        best_score = max(quality_scores) if quality_scores else 0
        dates_with_taken = sum(1 for photo in self.duplicates if photo.has_date_taken())
        photos_with_gps = sum(1 for photo in self.duplicates if photo.has_location())
        
        # Smart recommendation analysis
        recommended_photo = next((photo for photo in self.duplicates if photo.keep), None)
        recommendation_reason = ""
        
        if recommended_photo:
            reasons = []
            if recommended_photo.size == max(photo.size for photo in self.duplicates):
                reasons.append("largest file")
            if recommended_photo.has_title():
                reasons.append("has title")
            if recommended_photo.has_caption() or recommended_photo.has_keywords():
                reasons.append("rich metadata")
            if recommended_photo.has_location():
                reasons.append("has GPS")
            
            date_comp = recommended_photo.get_date_comparison()
            if date_comp['has_both_dates'] and date_comp['status'] in ['immediate', 'same_day']:
                reasons.append("uploaded soon after taking")
            
            if reasons:
                recommendation_reason = f" (recommended: {', '.join(reasons[:2])})"
        
        # Build header text
        header_parts = [
            f"Duplicate Group ({len(self.duplicates)} copies)",
            f"Wasting {waste_mb:.1f} MB"
        ]
        
        if best_score >= 5:
            header_parts.append(f"Quality range: {min(quality_scores)}-{best_score}")
        
        if dates_with_taken > 0:
            header_parts.append(f"{dates_with_taken} with date info")

        if photos_with_gps > 0:
            header_parts.append(f"{photos_with_gps} with GPS")
        
        header_text = " • ".join(header_parts) + recommendation_reason
        
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
        header.setWordWrap(True)
        return header
    
    def _create_photos_scroll_area(self) -> QScrollArea:
        """Create horizontal scroll area for photo cards"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(700)
        scroll_area.setMaximumHeight(1000)
        
        photos_widget = QWidget()
        photos_layout = QHBoxLayout(photos_widget)
        photos_layout.setSpacing(15)
        photos_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create cards for each duplicate photo
        for i, photo in enumerate(self.duplicates):
            card = self._create_photo_card(photo, i)
            photos_layout.addWidget(card)
        
        photos_layout.addStretch()
        scroll_area.setWidget(photos_widget)
        
        return scroll_area
    
    def _create_photo_card(self, photo: DuplicatePhoto, index: int) -> QWidget:
        """Create a card widget for a single photo - FIXED radio button behavior"""
        card = QWidget()
        card.setFixedWidth(320)
        
        # Calculate height based on metadata
        base_height = 650
        if photo.has_enhanced_metadata():
            extra_height = 50
            if photo.has_caption():
                extra_height += 60
            if photo.has_keywords():
                extra_height += 40 + (len(photo.get_keywords_list()) // 3) * 25
            if photo.has_date_taken():
                extra_height += 70
            if photo.has_location():
                extra_height += 50
            base_height += extra_height
        
        card.setMinimumHeight(base_height)
        
        # Store reference for later styling updates
        card.setProperty("photo_index", index)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # FIXED: Radio button creation with proper signal handling
        radio_text = "✅ Keep this copy"
        if photo.keep:
            score = photo.get_quality_score()
            if score >= 8:
                radio_text = "✅ Keep this copy (recommended - high quality)"
            elif score >= 5:
                radio_text = "✅ Keep this copy (recommended)"
        else:
            radio_text = "📦 Move to review album"
        
        radio = QRadioButton(radio_text)
        
        # CRITICAL FIX: Set initial state BEFORE adding to group and connecting signals
        radio.setChecked(photo.keep)
        
        # Add to button group with index
        self.button_group.addButton(radio, index)
        
        # Connect signal AFTER setup is complete - use lambda to pass index
        radio.toggled.connect(lambda checked, idx=index: self._on_radio_toggled(checked, idx))
        
        # Set styling
        self._update_radio_button_styling(radio, photo.keep)
        
        self.radio_buttons.append(radio)
        layout.addWidget(radio)
        
        # Photo preview
        preview = PhotoPreviewWidget()
        preview.setMinimumHeight(320)
        preview.setMaximumHeight(350)
        preview.display_photo(photo)
        self.preview_widgets.append(preview)
        layout.addWidget(preview)
        
        # All metadata (always visible)
        metadata_widget = self._create_all_metadata(photo)
        layout.addWidget(metadata_widget)
        
        layout.addStretch(1)
        
        # Set initial card styling
        self._update_card_styling_direct(card, photo.keep)
        
        return card

    def _on_radio_toggled(self, checked: bool, index: int):
        """Handle individual radio button toggle - FIXED version"""
        if not checked:  # Ignore unchecked events to avoid double processing
            return
            
        print(f"📻 Radio button {index} selected for {self.duplicates[index].filename}")
        
        # Update all photos in the group
        for i, photo in enumerate(self.duplicates):
            was_selected = photo.keep
            photo.keep = (i == index)
            
            # Update visual styling if state changed
            if was_selected != photo.keep:
                self._update_photo_card_styling(i)
        
        # Update all radio button text and styling
        self._update_all_radio_buttons()
        
        # Emit the selection changed signal
        self.selection_changed.emit()
        
        print(f"✅ Selection updated: keeping {self.duplicates[index].filename}")

    def _update_photo_card_styling(self, card_index: int):
        """Update visual styling of a photo card based on selection state"""
        try:
            photo = self.duplicates[card_index]
            radio = self.radio_buttons[card_index]
            card = radio.parent()
            
            self._update_card_styling_direct(card, photo.keep)
            self._update_radio_button_styling(radio, photo.keep)
            
        except Exception as e:
            print(f"Error updating card styling for index {card_index}: {e}")

    def _update_card_styling_direct(self, card: QWidget, is_selected: bool):
        """Update card styling directly"""
        base_style = """
            QWidget {
                background-color: #3c3c3c;
                border-radius: 8px;
                margin: 5px;
            }
        """
        
        if is_selected:
            card.setStyleSheet(base_style + """
                QWidget {
                    border: 2px solid #4CAF50;
                    background-color: #404040;
                }
            """)
        else:
            card.setStyleSheet(base_style + """
                QWidget {
                    border: 2px solid #555555;
                }
            """)

    def _update_radio_button_styling(self, radio: QRadioButton, is_selected: bool):
        """Update radio button styling"""
        if is_selected:
            radio.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50;")
        else:
            radio.setStyleSheet("font-weight: bold; font-size: 12px; color: #cccccc;")

    def _update_all_radio_buttons(self):
        """Update all radio button text and styling to reflect current selection state"""
        try:
            for i, (radio, photo) in enumerate(zip(self.radio_buttons, self.duplicates)):
                if photo.keep:
                    score = photo.get_quality_score()
                    if score >= 8:
                        radio.setText("✅ Keep this copy (recommended - high quality)")
                    elif score >= 5:
                        radio.setText("✅ Keep this copy (recommended)")
                    else:
                        radio.setText("✅ Keep this copy")
                    self._update_radio_button_styling(radio, True)
                else:
                    radio.setText("📦 Move to review album")
                    self._update_radio_button_styling(radio, False)
        except Exception as e:
            print(f"Error updating radio button text: {e}")
    
    def _create_all_metadata(self, photo: DuplicatePhoto) -> QWidget:
        """Create metadata display with all information always visible"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Format date with clear labeling
        try:
            if photo.date_uploaded and 'T' in photo.date_uploaded:
                from datetime import datetime
                dt = datetime.fromisoformat(photo.date_uploaded.replace('Z', '+00:00'))
                short_date = dt.strftime("%m/%d/%y")
                date_display = f"Uploaded: {short_date}"
            else:
                date_display = "Uploaded: Unknown"
        except:
            date_display = "Uploaded: Unknown"
        
        # Basic info lines (always visible)
        info_lines = [
            f"📁 {photo.short_album_name()}",
            f"📄 {photo.short_filename()}"
        ]
        
        # Add title display if present
        if photo.has_title():
            title_line = f"🏷️ {photo.display_title(28)}"
            info_lines.insert(1, title_line)

        # Add GPS coordinates to basic info if available
        if photo.has_location():
            location_line = f"🗺️ {photo.get_location_short()}"
            info_lines.append(location_line)
        
        # Add file size and date
        info_lines.append(f"📊 Size: {photo.size_mb():.1f} MB")
        info_lines.append(f"📤 {date_display}")
        
        # Add quality indicator
        quality_indicator = self._create_quality_indicator(photo)
        if quality_indicator:
            info_lines.append(quality_indicator)
        
        # Create basic metadata labels
        for line in info_lines:
            label = QLabel(line)
            
            if line.startswith("🏷️"):
                # Title styling
                label.setStyleSheet("""
                    font-size: 11px; color: #87CEEB; font-weight: bold;
                    padding: 4px 6px; background-color: rgba(60, 60, 60, 0.9);
                    border-radius: 4px; margin: 1px;
                    border: 1px solid rgba(135, 206, 235, 0.3);
                """)
            elif line.startswith("⭐"):
                # Quality indicator styling
                label.setStyleSheet("""
                    font-size: 10px; color: #FFD700; font-weight: bold;
                    padding: 3px 6px; background-color: rgba(50, 50, 50, 0.8);
                    border-radius: 4px; margin: 1px;
                    border: 1px solid rgba(255, 215, 0, 0.3);
                """)
            else:
                # Standard metadata styling
                label.setStyleSheet("""
                    font-size: 11px; color: #ffffff; padding: 4px 6px;
                    background-color: rgba(60, 60, 60, 0.9);
                    border-radius: 4px; margin: 1px;
                """)
            
            label.setWordWrap(True)
            layout.addWidget(label)
        
        # Enhanced metadata sections (always visible)
        if photo.has_enhanced_metadata():
            layout.addSpacing(6)
            
            # Date comparison section
            if photo.has_date_taken():
                date_section = self._create_date_comparison_section(photo)
                layout.addWidget(date_section)

            # Location section (detailed view)
            if photo.has_location():
                location_section = self._create_location_section(photo)
                layout.addWidget(location_section)
            
            # Caption section
            if photo.has_caption():
                caption_section = self._create_caption_section(photo)
                layout.addWidget(caption_section)
            
            # Keywords section
            if photo.has_keywords():
                keywords_section = self._create_keywords_section(photo)
                layout.addWidget(keywords_section)
        
        return widget
    
    def _create_date_comparison_section(self, photo: DuplicatePhoto) -> QWidget:
        """Create date comparison section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("📅 Photo Dates:")
        header.setStyleSheet("""
            font-size: 10px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 3px 6px;
            border-radius: 3px; margin-bottom: 2px;
        """)
        layout.addWidget(header)
        
        # Date info
        date_widget = QFrame()
        date_layout = QVBoxLayout(date_widget)
        date_layout.setSpacing(2)
        date_layout.setContentsMargins(6, 4, 6, 4)
        
        date_comp = photo.get_date_comparison()
        
        if date_comp['has_both_dates']:
            taken_lbl = QLabel(f"📸 Taken: {date_comp['date_taken_formatted']}")
            uploaded_lbl = QLabel(f"📤 Uploaded: {date_comp['date_uploaded_formatted']}")
            diff_lbl = QLabel(f"⏱️ {date_comp['time_difference']}")
            
            for lbl in [taken_lbl, uploaded_lbl]:
                lbl.setStyleSheet("""
                    font-size: 9px; color: #ffffff; padding: 2px;
                    background-color: rgba(60, 60, 60, 0.8); border-radius: 2px;
                """)
            
            diff_color = self._get_date_status_color(date_comp['status'])
            diff_lbl.setStyleSheet(f"""
                font-size: 9px; color: #ffffff; font-weight: bold; padding: 2px 4px; 
                background-color: {diff_color}; border-radius: 2px; margin: 1px;
            """)
            
            date_layout.addWidget(taken_lbl)
            date_layout.addWidget(uploaded_lbl)
            date_layout.addWidget(diff_lbl)
        else:
            if date_comp['date_taken_formatted']:
                lbl = QLabel(f"📸 Taken: {date_comp['date_taken_formatted']}")
            else:
                lbl = QLabel(f"📤 Uploaded: {date_comp['date_uploaded_formatted']}")
            
            lbl.setStyleSheet("""
                font-size: 9px; color: #ffffff; padding: 2px;
                background-color: rgba(60, 60, 60, 0.8); border-radius: 2px;
            """)
            date_layout.addWidget(lbl)
        
        date_widget.setStyleSheet("""
            QFrame { 
                background-color: rgba(45, 45, 45, 0.9); border: 1px solid #555555;
                border-radius: 3px; border-left: 3px solid #87CEEB; margin: 1px;
            }
        """)
        
        layout.addWidget(date_widget)
        return container
    
    def _create_location_section(self, photo: DuplicatePhoto) -> QWidget:
        """Create location/GPS section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("🗺️ Location:")
        header.setStyleSheet("""
            font-size: 10px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 3px 6px;
            border-radius: 3px; margin-bottom: 2px;
        """)
        layout.addWidget(header)

        # Location details
        location_widget = QFrame()
        location_layout = QVBoxLayout(location_widget)
        location_layout.setSpacing(2)
        location_layout.setContentsMargins(6, 4, 6, 4)

        # GPS coordinates
        coords_lbl = QLabel(f"🗺️ {photo.get_location_short()}")
        coords_lbl.setStyleSheet("""
            font-size: 9px; color: #ffffff; padding: 2px;
            background-color: rgba(60, 60, 60, 0.8); border-radius: 2px;
            font-family: monospace;
        """)
        location_layout.addWidget(coords_lbl)

        # Altitude if available
        if photo.altitude is not None:
            if photo.altitude >= 0:
                alt_text = f"⛰️ {photo.altitude:.0f}m above sea level"
            else:
                alt_text = f"🌊 {abs(photo.altitude):.0f}m below sea level"

            alt_lbl = QLabel(alt_text)
            alt_lbl.setStyleSheet("""
                font-size: 9px; color: #ffffff; padding: 2px;
                background-color: rgba(60, 60, 60, 0.8); border-radius: 2px;
            """)
            location_layout.addWidget(alt_lbl)

        location_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 45, 0.9); border: 1px solid #555555;
                border-radius: 3px; border-left: 3px solid #4CAF50; margin: 1px;
            }
        """)

        layout.addWidget(location_widget)
        return container
    
    def _create_caption_section(self, photo: DuplicatePhoto) -> QWidget:
        """Create caption section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("📝 Caption:")
        header.setStyleSheet("""
            font-size: 10px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 3px 6px;
            border-radius: 3px; margin-bottom: 2px;
        """)
        layout.addWidget(header)
        
        # Caption text
        caption_lbl = QLabel(photo.display_caption(150))
        caption_lbl.setWordWrap(True)
        caption_lbl.setStyleSheet("""
            font-size: 10px; color: #ffffff; padding: 4px;
            background-color: rgba(45, 45, 45, 0.9); border: 1px solid #555555;
            border-radius: 3px; border-left: 3px solid #87CEEB; 
            line-height: 1.3; min-height: 20px; margin: 1px;
        """)
        layout.addWidget(caption_lbl)
        
        return container
    
    def _create_keywords_section(self, photo: DuplicatePhoto) -> QWidget:
        """Create keywords section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        keyword_count = len(photo.get_keywords_list())
        header = QLabel(f"🏷️ Keywords ({keyword_count}):")
        header.setStyleSheet("""
            font-size: 10px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 3px 6px;
            border-radius: 3px; margin-bottom: 2px;
        """)
        layout.addWidget(header)
        
        # Keywords container
        kw_container = QFrame()
        kw_layout = QVBoxLayout(kw_container)
        kw_layout.setSpacing(3)
        kw_layout.setContentsMargins(6, 3, 6, 3)
        
        keywords = photo.get_keywords_list()
        for i in range(0, len(keywords), 3):
            row_keywords = keywords[i:i+3]
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(4)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            for keyword in row_keywords:
                tag = QLabel(keyword)
                tag.setStyleSheet("""
                    font-size: 8px; color: #ffffff; background-color: #4a90e2;
                    padding: 2px 6px; border-radius: 8px; font-weight: bold;
                    border: 1px solid #357abd; min-height: 12px;
                """)
                tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row_layout.addWidget(tag)
            
            row_layout.addStretch()
            kw_layout.addWidget(row_widget)
        
        kw_container.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 45, 0.9); border: 1px solid #555555;
                border-radius: 3px; border-left: 3px solid #4a90e2; 
                min-height: 25px; margin: 1px;
            }
        """)
        
        layout.addWidget(kw_container)
        return container
    
    def _get_date_status_color(self, status: str) -> str:
        """Get color for date status indication"""
        color_map = {
            'immediate': '#4CAF50',      # Green - likely original
            'same_day': '#8BC34A',       # Light green - very recent
            'recent': '#FFC107',         # Yellow - recent
            'delayed': '#FF9800',        # Orange - delayed
            'very_delayed': '#FF5722',   # Red-orange - very delayed
            'archived': '#9E9E9E',       # Gray - archived later
            'unknown': '#666666'         # Dark gray - unknown
        }
        return color_map.get(status, '#666666')
    
    def _create_quality_indicator(self, photo: DuplicatePhoto) -> str:
        """Create a quality indicator string for the photo"""
        score = photo.get_quality_score()
    
        if score >= 9:  # Increased threshold since GPS adds +1
            return "⭐ Premium Quality (recommended)"
        elif score >= 8:
            return "⭐ High Quality (recommended)"
        elif score >= 5:
            return "⭐ Good Quality"
        elif score >= 3:
            return "⭐ Standard Quality"
        elif score >= 1:
            return "⭐ Basic Quality"
        else:
            return ""

    def _create_status_feedback(self) -> QLabel:
        """Create status feedback label"""
        status_feedback = QLabel("")
        status_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_feedback.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0px;
                min-height: 20px;
            }
        """)
        status_feedback.setVisible(False)
        return status_feedback
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons layout"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Delete Unselected button
        delete_btn = QPushButton("🗑️ Delete Unselected Duplicates")
        delete_btn.clicked.connect(self.delete_selected_action)
        delete_btn.setToolTip("Permanently delete the photos that are NOT selected to keep")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet(self._get_delete_button_style())
        button_layout.addWidget(delete_btn)
        
        # Move to Review Album button
        move_btn = QPushButton("📦 Move to Review Album")
        move_btn.clicked.connect(self.move_selected_to_review_action)
        move_btn.setToolTip("Move unselected duplicates to review album (removes from source albums)")
        move_btn.setMinimumHeight(45)
        move_btn.setStyleSheet(self._get_move_button_style())
        button_layout.addWidget(move_btn)
        
        # Skip button
        skip_btn = QPushButton("🚫 Skip This Group")
        skip_btn.clicked.connect(self.skip_group_action)
        skip_btn.setToolTip("Skip this duplicate group - don't move or delete any copies")
        skip_btn.setMinimumHeight(45)
        skip_btn.setStyleSheet(self._get_skip_button_style())
        button_layout.addWidget(skip_btn)
        
        button_layout.addStretch()
        return button_layout
    
    # Action Methods
    def move_selected_to_review_action(self):
        """Move duplicates to review album using working moveimages"""
        try:
            import credentials
            from operations import EnhancedPhotoCopyMoveOperations
            
            # Get reference to the main window's API
            main_window = self.window()
            if not hasattr(main_window, 'api') or not main_window.api:
                self.show_feedback("❌ No API connection available", False)
                return
            
            # Determine which photos to move based on user selection
            selected_count = sum(1 for photo in self.duplicates if photo.keep)
            
            if selected_count == 0:
                photos_to_move = self.duplicates.copy()
                action_description = f"No photo selected to keep. Moving all {len(photos_to_move)} photos to review album."
                print(f"📦 {action_description}")
            elif selected_count == 1:
                photos_to_move = [photo for photo in self.duplicates if not photo.keep]
                kept_photo = [photo for photo in self.duplicates if photo.keep][0]
                action_description = f"Keeping {kept_photo.filename}. Moving {len(photos_to_move)} duplicate(s) to review album."
                print(f"📦 {action_description}")
                print(f"   ✅ KEEPING: {kept_photo.filename} from {kept_photo.album_name}")
                for photo in photos_to_move:
                    print(f"   📦 MOVING: {photo.filename} from {photo.album_name}")
            else:
                photos_to_move = self.duplicates.copy()
                action_description = f"Multiple photos selected (unusual). Moving all {len(photos_to_move)} photos to review album."
                print(f"⚠️ {action_description}")
            
            if not photos_to_move:
                self.show_feedback("✅ No photos need to be moved - all duplicates are selected to keep", True)
                return
            
            # Initialize enhanced move operations
            move_ops = EnhancedPhotoCopyMoveOperations(main_window.api)
            
            # Show processing feedback
            self.show_feedback(f"🔄 Moving {len(photos_to_move)} photo(s) with working moveimages...", None)
            
            # Process using working moveimages functionality
            results = move_ops.process_duplicates_for_review([photos_to_move], credentials.USER_NAME)
            
            if not results['success']:
                if results.get('manual_creation_needed'):
                    instructions = results.get('instructions', 'Manual album creation required')
                    album_name = results.get('suggested_album_name', 'SmugDups_Review')
                    
                    feedback_msg = f"📦 Create album manually: {album_name}"
                    self.show_feedback(feedback_msg, False)
                    
                    print(f"\n💡 MANUAL ALBUM CREATION NEEDED:")
                    print(instructions)
                    
                else:
                    error_msg = results.get('error', 'Unknown error occurred')
                    self.show_feedback(f"❌ Error: {error_msg}", False)
                
                return
            
            # Show results
            successful = results.get('successful_moves', 0)
            failed = results.get('failed_moves', 0)
            album_info = results['review_album']
            album_name = album_info['album_name']
            
            if successful > 0:
                if failed > 0:
                    success_msg = f"✅ Moved {successful}/{successful + failed} photos to {album_name}"
                    print(f"⚠️ {failed} photos failed to move - see console for details")
                else:
                    success_msg = f"🎉 All {successful} photos moved to {album_name}!"
                
                self.show_feedback(success_msg, True)
                
                if album_info.get('web_url'):
                    print(f"🌐 Review album: {album_info['web_url']}")
                    
            else:
                if failed > 0:
                    failure_msg = f"❌ Failed to move {failed} photos. Check console for details."
                    self.show_feedback(failure_msg, False)
                    
                    if album_info.get('web_url'):
                        print(f"💡 Manual moving instructions:")
                        print(f"   1. Visit: {album_info['web_url']}")
                        print(f"   2. Use SmugMug's 'Move' or 'Organize' feature to move these photos:")
                        for photo in photos_to_move:
                            print(f"      - {photo.filename} from {photo.album_name}")
                else:
                    manual_msg = f"📦 Photos need manual moving to {album_name}"
                    self.show_feedback(manual_msg, None)
            
            if successful > 0:
                self.mark_as_processed()
                
        except Exception as e:
            error_msg = f"💥 Move error: {e}"
            self.show_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    def delete_selected_action(self):
        """Handle the delete selected action"""
        selected_count = sum(1 for photo in self.duplicates if photo.keep)
        to_delete_count = len(self.duplicates) - selected_count
        
        if selected_count == 0:
            self.show_feedback("❌ Error: No photo selected to keep!", False)
            return
        elif selected_count > 1:
            self.show_feedback("❌ Error: Multiple photos selected to keep!", False)
            return
        
        photos_to_delete = [photo for photo in self.duplicates if not photo.keep]
        photos_to_keep = [photo for photo in self.duplicates if photo.keep]
        
        print(f"\n🗑️ PERMANENT DELETION STARTING...")
        print(f"Will delete {to_delete_count} photos, keeping 1")
        
        for photo in photos_to_keep:
            print(f"  ✅ KEEP: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        for photo in photos_to_delete:
            print(f"  🗑️ DELETE: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        self.show_feedback(f"🔄 Deleting {to_delete_count} duplicate photo(s)...", None)
        
        try:
            main_window = self.window()
            api = main_window.api
            
            deletion_results = []
            for photo in photos_to_delete:
                print(f"\n🔄 Deleting {photo.filename} (ID: {photo.image_id})...")
                
                success = False
                error_message = ""
                max_retries = 3
                
                for attempt in range(max_retries):
                    if attempt > 0:
                        print(f"Retry attempt {attempt + 1}/{max_retries}")
                        import time
                        time.sleep(2)
                    
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
            
            successful_deletions = [r for r in deletion_results if r[1]]
            failed_deletions = [r for r in deletion_results if not r[1]]
            
            print(f"\n📊 DELETION SUMMARY:")
            print(f"✅ Successfully deleted: {len(successful_deletions)} photos")
            print(f"❌ Failed to delete: {len(failed_deletions)} photos")
            
            if successful_deletions:
                success_msg = f"✅ Successfully deleted {len(successful_deletions)} duplicate photo(s)!"
                self.show_feedback(success_msg, True)
            else:
                failure_msg = "❌ No photos were deleted. Check console for details."
                self.show_feedback(failure_msg, False)
                
        except Exception as e:
            error_msg = f"💥 Error during deletion: {e}"
            self.show_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    def skip_group_action(self):
        """Mark this duplicate group to be skipped"""
        for i, radio in enumerate(self.radio_buttons):
            radio.setChecked(False)
            self.duplicates[i].keep = False
        
        header_widget = self.findChild(QLabel)
        if header_widget and "Duplicate Group" in header_widget.text():
            original_text = header_widget.text()
            header_widget.setText(f"🚫 SKIPPED: {original_text}")
            header_widget.setStyleSheet(header_widget.styleSheet().replace(
                'color: #ff6b6b',
                'color: #888888'
            ))
        
        for button in self.findChildren(QPushButton):
            if "Skip" not in button.text():
                button.setEnabled(False)
        
        self.selection_changed.emit()
    
    # UI Helper Methods
    def show_feedback(self, message: str, success: Optional[bool]):
        """Show feedback in the GUI"""
        self.status_feedback.setVisible(True)
        self.status_feedback.setText(message)
        
        if success is None:  # Processing
            style = """
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 8px; border-radius: 4px;
                    margin: 5px 0px; min-height: 20px; background-color: #e3f2fd;
                    color: #1565c0; border: 1px solid #2196f3;
                }
            """
        elif success:  # Success
            style = """
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 8px; border-radius: 4px;
                    margin: 5px 0px; min-height: 20px; background-color: #e8f5e8;
                    color: #2e7d32; border: 1px solid #4caf50;
                }
            """
            for button in self.findChildren(QPushButton):
                button.setEnabled(False)
        else:  # Error
            style = """
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 8px; border-radius: 4px;
                    margin: 5px 0px; min-height: 20px; background-color: #ffebee;
                    color: #c62828; border: 1px solid #f44336;
                }
            """
        
        self.status_feedback.setStyleSheet(style)
    
    def mark_as_processed(self):
        """Mark this group as processed"""
        header_widget = self.findChild(QLabel)
        if header_widget and "Duplicate Group" in header_widget.text():
            original_text = header_widget.text()
            header_widget.setText(f"✅ PROCESSED: {original_text}")
            header_widget.setStyleSheet(header_widget.styleSheet().replace(
                'color: #ff6b6b',
                'color: #4CAF50'
            ))
        
        for button in self.findChildren(QPushButton):
            button.setEnabled(False)
    
    # Style Methods
    def _get_delete_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #d32f2f; border: 1px solid #f44336;
                font-weight: bold; font-size: 13px; color: white;
            }
            QPushButton:hover { background-color: #f44336; }
            QPushButton:pressed { background-color: #c62828; }
        """
    
    def _get_move_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #4CAF50; border: 1px solid #45a049;
                font-weight: bold; font-size: 13px; color: white;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """
    
    def _get_skip_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #6c6c6c; border: 1px solid #888888;
                font-weight: bold; color: white;
            }
            QPushButton:hover { background-color: #7c7c7c; }
            QPushButton:pressed { background-color: #8c8c8c; }
        """

    # DEBUGGING METHOD
    def debug_radio_state(self):
        """Debug method to check radio button and photo state alignment"""
        print(f"\n🔍 DEBUG: Radio button state for group with {len(self.duplicates)} photos:")
        for i, (radio, photo) in enumerate(zip(self.radio_buttons, self.duplicates)):
            radio_checked = radio.isChecked()
            photo_keep = photo.keep
            match = "✅" if radio_checked == photo_keep else "❌"
            print(f"  {i}: {photo.filename[:30]:<30} Radio:{radio_checked} Photo:{photo_keep} {match}")
        
        # Check button group state
        checked_button = self.button_group.checkedButton()
        if checked_button:
            checked_index = self.button_group.id(checked_button)
            print(f"  ButtonGroup selected index: {checked_index}")
        else:
            print(f"  ButtonGroup: No button selected")
