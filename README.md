# SmugDups v5.0 - SmugMug Duplicate Photo Manager

**Advanced duplicate photo detection and management for SmugMug accounts with working moveimages functionality.**

![SmugDups v5.0](https://img.shields.io/badge/Version-5.0-brightgreen) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-orange) ![SmugMug API](https://img.shields.io/badge/API-SmugMug%20v2-red)

## 🎉 What's New in v5.0

- **✅ WORKING moveimages functionality** - True moves with no manual cleanup needed!
- **✅ SmugMug API v2 compliant** - Uses proper parameters discovered through support collaboration
- **✅ Automatic verification** - Confirms moves actually worked
- **✅ Enhanced error handling** - Robust OAuth and redirect management
- **🚀 Original idea from MugMatch updated and refactored to SmugDups** - New name, same powerful functionality!

## 🚀 Features

### Core Functionality
- **MD5-based duplicate detection** across multiple SmugMug albums
- **True moveimages support** - duplicates are removed from source albums
- **Automatic review album creation** with date-stamped naming
- **No manual cleanup required** - fully automated workflow

### User Interface
- **Modern PyQt6 GUI** with dark theme
- **Photo preview thumbnails** with metadata display
- **Batch album selection** with sorting options
- **Real-time progress tracking** during scans
- **Intuitive duplicate management** with radio button selection

### Technical Excellence
- **OAuth1 authentication** with proper redirect handling
- **SmugMug API v2 integration** using confirmed working parameters
- **Modular architecture** for maintainability
- **Comprehensive error handling** and logging
- **Rate limiting** to respect API guidelines

## 📋 Prerequisites

- **Python 3.9+**
- **SmugMug account** with API access
- **SmugMug API credentials** (API key, secret, access tokens)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/xtremetoonz/SmugDups.git
   cd SmugDups
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up credentials:**
   ```bash
   cp credentialsTemplate.py credentials.py
   # Edit credentials.py with your SmugMug API details
   ```

## 🔑 SmugMug API Setup

1. **Get API credentials:**
   - Visit [SmugMug API](https://api.smugmug.com/api/developer/apply)
   - Apply for API access
   - Note your API Key and Secret

2. **Get access tokens:**
   - Use SmugMug's OAuth flow to get access tokens
   - Add all credentials to `credentials.py`

3. **Required permissions:**
   - Read access to albums and images
   - Modify access for moving images
   - Create access for review albums

## 🚀 Usage

### Basic Workflow

1. **Launch SmugDups:**
   ```bash
   python main.py
   ```

2. **Select albums** to scan from the left panel
3. **Click "Scan for Duplicates"** to find duplicates
4. **Review duplicate groups** and select which copies to keep
5. **Click "Move to Review Album"** to move duplicates (working moveimages!)

### Advanced Features

- **Album sorting** by name, photo count, or date
- **Batch selection** with "All" and "None" buttons
- **Skip duplicate groups** you want to leave unchanged
- **Permanent deletion** option for immediate removal

## 📦 Project Structure

```
SmugDups/
├── main.py                          # Entry point
├── smugmug_api.py                   # SmugMug API wrapper with OAuth
├── credentials.py                   # Your API keys (create from template)
├── requirements.txt                 # Python dependencies
├── core/
│   ├── models.py                    # DuplicatePhoto data model
│   └── duplicate_finder.py          # Background duplicate detection
├── gui/
│   ├── main_window.py              # Main application window
│   ├── duplicate_widget.py         # Duplicate group management UI
│   └── photo_preview.py            # Photo thumbnail display
└── operations/
    ├── enhanced_photo_copy_move.py  # Main orchestrator with working moves
    ├── smugmug_copy_operations.py   # Core move operations
    └── smugmug_album_operations.py  # Album management
```

## ⚙️ Configuration

### credentials.py Template
```python
# SmugMug API credentials
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"
ACCESS_TOKEN = "your_access_token_here"
ACCESS_SECRET = "your_access_secret_here"
USER_NAME = "your_smugmug_username"
```

### Key Settings
- **Review album naming:** `SmugDups Review YYYYMMDD`
- **Duplicate detection:** MD5 hash comparison
- **Move verification:** Automatic confirmation
- **Rate limiting:** 1 second between operations

## 🔧 Technical Details

### Working MoveImages Implementation
SmugDups v5.0 uses the correct SmugMug API v2 moveimages format:

```python
# Correct moveimages format (discovered through SmugMug support):
url = f"https://api.smugmug.com/api/v2/album/{target_album}!moveimages"
data = {
    'MoveUris': f"/api/v2/album/{source_album}/image/{image_id}-0"
}
```

### Key Technical Insights
- **Parameter name:** `MoveUris` (not `ImageUris`)
- **URI format:** AlbumImage URI format (`/api/v2/album/SOURCE/image/ID`)
- **Endpoint:** Use target album's moveimages endpoint
- **Verification:** Check source no longer has image and target does

### OAuth and Redirects
SmugDups handles SmugMug's OAuth redirects properly:
- Disables automatic redirects (`allow_redirects=False`)
- Creates fresh OAuth tokens for redirect requests
- Follows SmugMug engineering guidance

## 🐛 Troubleshooting

### Common Issues

**"No API connection"**
- Check credentials.py file exists and has correct values
- Verify API key permissions include Read and Modify access

**"Album not accessible"**
- Ensure albums exist and are accessible to your API key
- Check album privacy settings

**"Move operation failed"**
- Verify images exist in source albums
- Check that target album allows image additions
- Review console output for specific error messages

### Debug Mode
Enable detailed logging by checking console output during operations.

## 📈 Performance

- **Scan speed:** ~100 images per second (network dependent)
- **Memory usage:** Minimal (thumbnails cached locally)
- **API compliance:** Rate limited to respect SmugMug guidelines
- **Move verification:** Automatic confirmation of successful operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with your SmugMug account
5. Submit a pull request

### Development Guidelines
- Follow existing code structure
- Add comprehensive error handling
- Test with real SmugMug data
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SmugMug Support Team** for helping solve the moveimages parameter format
- **SmugMug API Team** for maintaining comprehensive API documentation
- **PyQt6 Community** for excellent GUI framework
- **Original SmugDups inspiration** that led to this enhanced version

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/xtremetoonz/SmugDups/issues)
- **Discussions:** [GitHub Discussions](https://github.com/xtremetoonz/SmugDups/discussions)
- **Email:** Check GitHub profile for contact information

## 🗺️ Roadmap

### Planned Features
- **Batch operations** for large duplicate sets
- **Advanced filtering** by file type, size, date
- **Duplicate prevention** during uploads
- **Integration** with other photo services
- **Automated scheduling** for regular scans

### Version History
- **v5.0:** Working moveimages, rebranded to SmugDups
- **v2.x:** Collectimages approach
- **v1.x:** Initial duplicate detection implementation

---

**SmugDups v5.0** - Making SmugMug duplicate management simple and effective! 🎉

*"Finally, true moveimages functionality that actually works!"*
