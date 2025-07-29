# SmugDups

A Python-based desktop application for finding and managing duplicate photos in SmugMug accounts.

## Features
- 🔍 **Duplicate Detection**: MD5 hash-based duplicate identification across albums
- 🖼️ **Visual Review**: PyQt6 interface with photo previews and metadata
- 📁 **Album Management**: Auto-creates review albums for duplicate management
- 🔄 **SmugMug Integration**: OAuth1 authentication with proper redirect handling
- 🎯 **Selective Management**: Choose which duplicates to keep/move

## Project Structure
```
SmugDups/
├── main.py                           # Application entry point
├── smugmug_api.py                    # SmugMug API wrapper
├── requirements.txt                  # Python dependencies
├── core/
│   ├── models.py                     # Data models
│   └── duplicate_finder.py           # Duplicate detection logic
├── gui/
│   ├── main_window.py               # Main application window
│   ├── duplicate_widget.py          # Duplicate management UI
│   └── photo_preview.py             # Photo display widgets
└── operations/
    ├── __init__.py                  # Package initialization
    ├── enhanced_photo_copy_move.py  # Main orchestrator
    ├── smugmug_copy_operations.py   # Image operations
    └── smugmug_album_operations.py  # Album management
```

## Setup
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Credentials**: Copy `credentialsTemplate.py` to `credentials.py` and add your SmugMug API keys
3. **Run Application**: `python3 main.py`

## Current Status (v2.7)
- ✅ Duplicate detection working
- ✅ GUI interface complete
- ✅ SmugMug OAuth authentication working
- 🔄 Image moving functionality in development

## Development Notes
- Built with PyQt6 for modern GUI
- Uses SmugMug API v2 with OAuth1 authentication
- Modular architecture for easy maintenance
- Safe-mode operations to prevent data loss

## Contributing
This is a personal project for managing SmugMug photo duplicates. Feel free to fork and adapt for your needs.

## License
MIT License - See LICENSE file for details
