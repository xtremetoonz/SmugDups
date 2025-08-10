"""
Simplified expandable metadata widget - NO individual buttons
File: gui/expandable_metadata.py
UPDATED: Controlled by group-level toggle only
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from core.models import DuplicatePhoto

class ExpandableMetadataWidget(QWidget):
    """Simplified expandable widget controlled by group-level button"""
    
    def __init__(self, photo: DuplicatePhoto):
        super().__init__()
        self.photo = photo
        self.expanded = False
        self.animation = None
        self.content_built = False
        
        # Skip entirely if no enhanced metadata
        if not photo.has_enhanced_metadata():
            self.setMaximumHeight(0)
            self.setVisible(False)
            return
            
        self._create_simple_container()
    
    def _create_simple_container(self):
        """Create simple container without individual buttons"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # Create details container (starts collapsed)
        self.details = QFrame()
        self.details.setMaximumHeight(0)
        self.details.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 2px solid #555555;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        
        layout.addWidget(self.details)
    
    def toggle_expansion(self):
        """Toggle expansion - called by group controller"""
        print(f"Toggling expansion for {self.photo.filename}, currently: {self.expanded}")
        
        if not self.content_built:
            self._build_content()
        
        target_expanded = not self.expanded
        
        if target_expanded:
            # Expanding
            self.expanded = True
            self.details.setMaximumHeight(9999)
            self.details.updateGeometry()
            
            if self.details.layout():
                self.details.layout().activate()
            
            target_height = max(200, self.details.sizeHint().height())
            print(f"Expanding {self.photo.filename} to height: {target_height}")
        else:
            # Collapsing
            self.expanded = False
            target_height = 0
            print(f"Collapsing {self.photo.filename}")
        
        self._animate_to_height(target_height)
    
    def _animate_to_height(self, target_height):
        """Animate to target height"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self.details, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.setStartValue(self.details.maximumHeight())
        self.animation.setEndValue(target_height)
        
        def on_finished():
            if self.expanded:
                self.details.setMaximumHeight(9999)
                self.details.setVisible(True)
                self.details.show()
            else:
                self.details.setMaximumHeight(0)
            print(f"{self.photo.filename} animation complete, expanded: {self.expanded}")
        
        self.animation.finished.connect(on_finished)
        self.animation.start()
    
    def _build_content(self):
        """Build expandable content"""
        if self.content_built:
            return
        
        layout = QVBoxLayout(self.details)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Date comparison section
        if self.photo.has_date_taken():
            layout.addWidget(self._create_date_section())
        
        # Caption section  
        if self.photo.has_caption():
            layout.addWidget(self._create_caption_section())
        
        # Keywords section
        if self.photo.has_keywords():
            layout.addWidget(self._create_keywords_section())
        
        layout.addSpacing(10)
        self.content_built = True
        print(f"Content built for {self.photo.filename}")
    
    def _create_date_section(self):
        """Create date comparison section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        header = QLabel("📅 Photo Dates:")
        header.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 4px 8px;
            border-radius: 3px; margin-bottom: 3px;
        """)
        layout.addWidget(header)
        
        date_widget = QFrame()
        date_layout = QVBoxLayout(date_widget)
        date_layout.setSpacing(4)
        date_layout.setContentsMargins(10, 8, 10, 8)
        
        date_comp = self.photo.get_date_comparison()
        
        if date_comp['has_both_dates']:
            taken_lbl = QLabel(f"📸 Taken: {date_comp['date_taken_formatted']}")
            uploaded_lbl = QLabel(f"📤 Uploaded: {date_comp['date_uploaded_formatted']}")
            diff_lbl = QLabel(f"⏱️ {date_comp['time_difference']}")
            
            for lbl in [taken_lbl, uploaded_lbl]:
                lbl.setStyleSheet("""
                    font-size: 10px; color: #ffffff; padding: 3px;
                    background-color: rgba(60, 60, 60, 0.8); border-radius: 2px; margin: 1px;
                """)
            
            diff_color = self._get_date_color(date_comp['status'])
            diff_lbl.setStyleSheet(f"""
                font-size: 10px; color: #ffffff; font-weight: bold; padding: 4px 6px; 
                background-color: {diff_color}; border-radius: 3px; margin: 2px;
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
                font-size: 10px; color: #ffffff; padding: 4px;
                background-color: rgba(60, 60, 60, 0.8); border-radius: 2px;
            """)
            date_layout.addWidget(lbl)
        
        date_widget.setStyleSheet("""
            QFrame { 
                background-color: rgba(45, 45, 45, 0.9); border: 1px solid #666666;
                border-radius: 4px; border-left: 4px solid #87CEEB; 
            }
        """)
        
        layout.addWidget(date_widget)
        return container
    
    def _create_caption_section(self):
        """Create caption section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        header = QLabel("📝 Caption:")
        header.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 4px 8px;
            border-radius: 3px; margin-bottom: 3px;
        """)
        layout.addWidget(header)
        
        caption_lbl = QLabel(self.photo.display_caption(200))
        caption_lbl.setWordWrap(True)
        caption_lbl.setStyleSheet("""
            font-size: 11px; color: #ffffff; padding: 8px;
            background-color: rgba(45, 45, 45, 0.9); border: 1px solid #666666;
            border-radius: 4px; border-left: 4px solid #87CEEB; 
            line-height: 1.4; min-height: 30px;
        """)
        layout.addWidget(caption_lbl)
        
        return container
    
    def _create_keywords_section(self):
        """Create keywords section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        keyword_count = len(self.photo.get_keywords_list())
        header = QLabel(f"🏷️ Keywords ({keyword_count}):")
        header.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #ffffff;
            background-color: rgba(70, 70, 70, 0.8); padding: 4px 8px;
            border-radius: 3px; margin-bottom: 3px;
        """)
        layout.addWidget(header)
        
        kw_container = QFrame()
        kw_layout = QVBoxLayout(kw_container)
        kw_layout.setSpacing(5)
        kw_layout.setContentsMargins(10, 8, 10, 8)
        
        keywords = self.photo.get_keywords_list()
        for i in range(0, len(keywords), 3):
            row_keywords = keywords[i:i+3]
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(6)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            for keyword in row_keywords:
                tag = QLabel(keyword)
                tag.setStyleSheet("""
                    font-size: 10px; color: #ffffff; background-color: #4a90e2;
                    padding: 4px 10px; border-radius: 12px; font-weight: bold;
                    border: 1px solid #357abd; min-height: 16px;
                """)
                tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row_layout.addWidget(tag)
            
            row_layout.addStretch()
            kw_layout.addWidget(row_widget)
        
        kw_container.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 45, 0.9); border: 1px solid #666666;
                border-radius: 4px; border-left: 4px solid #4a90e2; min-height: 40px;
            }
        """)
        
        layout.addWidget(kw_container)
        return container
    
    def _get_date_color(self, status):
        """Get color for date status"""
        colors = {
            'immediate': '#4CAF50', 'same_day': '#8BC34A', 'recent': '#FFC107',
            'delayed': '#FF9800', 'very_delayed': '#FF5722', 'archived': '#9E9E9E'
        }
        return colors.get(status, '#666666')
