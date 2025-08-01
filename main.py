#!/usr/bin/env python3
"""
SmugDups - SmugMug Duplicate Photo Manager v5.0
File: main.py
Entry point for the SmugDups application - NOW WITH WORKING MOVEIMAGES!
"""

import sys
import warnings

# Suppress SSL warnings on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')

from PyQt6.QtWidgets import QApplication
from gui.main_window import SmugDupsMainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("SmugDups")
    app.setApplicationVersion("5.0")
    app.setOrganizationName("SmugDups")
    
    # Create and show main window
    window = SmugDupsMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    print("🚀 Starting SmugDups v5.0 - SmugMug Duplicate Photo Manager")
    print("✅ Now with WORKING moveimages functionality!")
    main()
