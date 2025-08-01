"""
Widget to display and manage a group of duplicate photos for SmugDups v5.0
File: gui/duplicate_widget.py
UPDATED: Rebranded from SmugDups and now uses WORKING moveimages
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from core.models import DuplicatePhoto
from .photo_preview import PhotoPreviewWidget

class DuplicateGroupWidget(QWidget):
    """Widget to display and manage a group of duplicate photos - SmugDups v5.0"""
    
    selection_changed = pyqtSignal()
    
    def __init__(self, duplicates: List[DuplicatePhoto]):
        super().__init__()
        self.duplicates = duplicates
        self.radio_buttons = []
        self.button_group = QButtonGroup()
        self.preview_widgets = []
        self._setup_ui()
    
    def debug_selection_state(self):
        """Debug method to show current selection state"""
        print(f"\n🔍 DEBUG: Selection state for duplicate group:")
        for i, photo in enumerate(self.duplicates):
            status = "KEEP" if photo.keep else "MOVE"
            print(f"   {i}: {photo.filename} from {photo.album_name} → {status}")
        
        selected_count = sum(1 for photo in self.duplicates if photo.keep)
        print(f"   Total selected to keep: {selected_count}")
        print(f"   Total to move: {len(self.duplicates) - selected_count}")
        
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Group header with summary
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
        """Create the group header with summary information"""
        waste_size = sum(photo.size for photo in self.duplicates[1:])
        waste_mb = waste_size / (1024*1024)
        header_text = f"Duplicate Group ({len(self.duplicates)} copies) - Wasting {waste_mb:.1f} MB"
        
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
        return header
    
    def _create_photos_scroll_area(self) -> QScrollArea:
        """Create horizontal scroll area with photo cards"""
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
            card = self._create_photo_card(photo, i)
            photos_layout.addWidget(card)
            
        # Add stretch to push cards to the left
        photos_layout.addStretch()
            
        scroll_area.setWidget(photos_widget)
        return scroll_area
    
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
        """Create the action buttons layout - UPDATED FOR WORKING MOVES"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Delete Selected button (permanent deletion)
        delete_btn = QPushButton("🗑️ Delete Selected Duplicates")
        delete_btn.clicked.connect(self.delete_selected_action)
        delete_btn.setToolTip("Permanently delete the photos that are NOT selected to keep")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet(self._get_delete_button_style())
        button_layout.addWidget(delete_btn)
        
        # UPDATED: Move to Review Album button (now with WORKING moves!)
        move_btn = QPushButton("📦 Move to Review Album")
        move_btn.clicked.connect(self.move_selected_to_review_action)
        move_btn.setToolTip("Move duplicates to review album (removes from source albums) - NOW WITH WORKING MOVEIMAGES!")
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
    
    def _create_photo_card(self, photo: DuplicatePhoto, index: int) -> QWidget:
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
        radio.toggled.connect(self._on_selection_changed)
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
        metadata_widget = self._create_compact_metadata(photo)
        layout.addWidget(metadata_widget)
        
        layout.addStretch()
        return card
    
    def _create_compact_metadata(self, photo: DuplicatePhoto) -> QWidget:
        """Create compact metadata display below photo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
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
            f"📁 {photo.short_album_name()}",
            f"📄 {photo.short_filename()}",
            f"📊 {photo.size_mb():.1f} MB  📅 {short_date}"
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
    
    def _on_selection_changed(self):
        """Handle radio button selection change"""
        for i, radio in enumerate(self.radio_buttons):
            self.duplicates[i].keep = radio.isChecked()
        self.selection_changed.emit()
    
    # Action Methods - UPDATED FOR WORKING MOVEIMAGES
    def move_selected_to_review_action(self):
        """Move duplicates to review album using WORKING moveimages - SmugDups v5.0"""
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
                # No photo selected to keep - move all to review for manual decision
                photos_to_move = self.duplicates.copy()
                action_description = f"No photo selected to keep. Moving all {len(photos_to_move)} photos to review album."
                print(f"📦 {action_description}")
            elif selected_count == 1:
                # One photo selected to keep - move only the others to review  
                photos_to_move = [photo for photo in self.duplicates if not photo.keep]
                kept_photo = [photo for photo in self.duplicates if photo.keep][0]
                action_description = f"Keeping {kept_photo.filename}. Moving {len(photos_to_move)} duplicate(s) to review album."
                print(f"📦 {action_description}")
                print(f"   ✅ KEEPING: {kept_photo.filename} from {kept_photo.album_name}")
                for photo in photos_to_move:
                    print(f"   📦 MOVING: {photo.filename} from {photo.album_name}")
            else:
                # Multiple photos selected - this shouldn't happen with radio buttons, but handle it
                photos_to_move = self.duplicates.copy()
                action_description = f"Multiple photos selected (unusual). Moving all {len(photos_to_move)} photos to review album."
                print(f"⚠️  {action_description}")
            
            if not photos_to_move:
                self.show_feedback("✅ No photos need to be moved - all duplicates are selected to keep", True)
                return
            
            # Initialize enhanced move operations with WORKING moveimages
            move_ops = EnhancedPhotoCopyMoveOperations(main_window.api)
            
            # Show processing feedback
            self.show_feedback(f"🔄 Moving {len(photos_to_move)} photo(s) with WORKING moveimages...", None)
            
            # Process using WORKING moveimages functionality
            results = move_ops.process_duplicates_for_review([photos_to_move], credentials.USER_NAME)
            
            if not results['success']:
                if results.get('manual_creation_needed'):
                    # Show manual creation instructions
                    instructions = results.get('instructions', 'Manual album creation required')
                    album_name = results.get('suggested_album_name', 'SmugDups_Review')
                    
                    feedback_msg = f"📦 Create album manually: {album_name}"
                    self.show_feedback(feedback_msg, False)
                    
                    # Print detailed instructions to console
                    print(f"\n💡 MANUAL ALBUM CREATION NEEDED:")
                    print(instructions)
                    
                else:
                    error_msg = results.get('error', 'Unknown error occurred')
                    self.show_feedback(f"❌ Error: {error_msg}", False)
                
                return
            
            # Show results for WORKING moveimages
            successful = results.get('successful_moves', 0)
            failed = results.get('failed_moves', 0)
            album_info = results['review_album']
            album_name = album_info['album_name']
            
            if successful > 0:
                if failed > 0:
                    success_msg = f"✅ Moved {successful}/{successful + failed} photos to {album_name}"
                    print(f"⚠️  {failed} photos failed to move - see console for details")
                else:
                    success_msg = f"🎉 All {successful} photos moved to {album_name}!"
                
                self.show_feedback(success_msg, True)
                
                # Show review album URL if available
                if album_info.get('web_url'):
                    print(f"🌐 Review album: {album_info['web_url']}")
                    
            else:
                # All moves failed - provide helpful guidance
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
                    # This shouldn't happen, but handle it
                    manual_msg = f"📦 Photos need manual moving to {album_name}"
                    self.show_feedback(manual_msg, None)
            
            # Mark as processed if moves were successful
            if successful > 0:
                self.mark_as_processed()
                
        except Exception as e:
            error_msg = f"💥 Move error: {e}"
            self.show_feedback(error_msg, False)
            import traceback
            traceback.print_exc()
    
    # Keep the old method name for backwards compatibility during transition
    def copy_selected_to_review_action(self):
        """Backwards compatibility - redirects to move action"""
        print("⚠️  WARNING: copy_selected_to_review_action is deprecated!")
        print("   🎯 Now using move_selected_to_review_action for WORKING moves")
        self.move_selected_to_review_action()
            
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
        
        # Show what will be deleted
        photos_to_delete = [photo for photo in self.duplicates if not photo.keep]
        photos_to_keep = [photo for photo in self.duplicates if photo.keep]
        
        print(f"\n🗑️  PERMANENT DELETION STARTING...")
        print(f"Will delete {to_delete_count} photos, keeping 1")
        
        for photo in photos_to_keep:
            print(f"  ✅ KEEP: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        for photo in photos_to_delete:
            print(f"  🗑️  DELETE: {photo.filename} from {photo.album_name} (ID: {photo.image_id})")
        
        # Show processing feedback
        self.show_feedback(f"🔄 Deleting {to_delete_count} duplicate photo(s)...", None)
        
        # Perform actual deletion using the fixed API
        try:
            # Get API reference from main window
            main_window = self.window()
            api = main_window.api
            
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
            
            # Show GUI feedback
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
            # Disable buttons after success
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
    
    def _get_move_button_style(self) -> str:  # RENAMED from _get_copy_button_style
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
