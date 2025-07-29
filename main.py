#!/usr/bin/env python3
"""
MugMatch - SmugMug Duplicate Photo Manager v2.1
File: main.py
Entry point for the modernized MugMatch application
"""

import sys
import warnings

# Suppress SSL warnings on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')

from PyQt6.QtWidgets import QApplication
from gui.main_window import MugMatchMainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MugMatch")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("MugMatch")
    
    # Create and show main window
    window = MugMatchMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
