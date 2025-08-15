# SmugDups v5.1 - SmugMug Duplicate Photo Manager

**Advanced duplicate photo detection and management for SmugMug accounts with working moveimages functionality and GPS coordinate support.**

![SmugDups v5.1](https://img.shields.io/badge/Version-5.1-brightgreen) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-orange) ![SmugMug API](https://img.shields.io/badge/API-SmugMug%20v2-red)

## ✨ What's New in v5.1

- **🗺️ GPS Coordinate Support** - Display latitude, longitude, and altitude when available
- **📍 Enhanced Quality Scoring** - GPS-tagged photos get higher quality scores  
- **🌍 Location-Based Decision Making** - See which duplicates have geographic data
- **📊 Geographic Statistics** - Group headers show GPS data availability
- **🔧 FIXED: Radio Button Selection** - Photo selection now works properly
- **✅ All v5.0 Features** - Working moveimages, automatic verification, enhanced error handling

## 🚀 Features

### Core Functionality
- **MD5-based duplicate detection** across multiple SmugMug albums
- **True moveimages support** - duplicates are removed from source albums
- **Automatic review album creation** with date-stamped naming
- **No manual cleanup required** - fully automated workflow

### Geographic Enhancement (v5.1)
- **GPS coordinate display** - latitude, longitude, altitude when available
- **Location-aware quality scoring** - GPS data contributes to duplicate selection
- **Smart location display** - compact coordinates in basic view, detailed in expanded
- **Distance calculations** - calculate distances between geotagged duplicates

### User Interface
- **Modern PyQt6 GUI** with dark theme
- **Photo preview thumbnails** with metadata display
- **Batch album selection** with sorting options
- **Real-time progress tracking** during scans
- **Fixed duplicate management** with working radio button selection
- **Geographic data integration** - seamless GPS coordinate display

### Technical Excellence
- **OAuth1 authentication** with proper redirect handling
- **SmugMug API v2 integration** using confirmed working parameters
- **Modular architecture** for maintainability
- **Comprehensive error handling** and logging
- **Rate limiting** to respect API guidelines

## 📋 Prerequisites

- **Python 3.9+** (tested on Python 3.13.5)
- **SmugMug account** with API access
- **SmugMug API credentials** (API key, secret, access tokens)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/xtremetoonz/SmugDups.git
   cd SmugDups
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv smugdups_env
   source smugdups_env/bin/activate  # On Windows: smugdups_env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up credentials:**
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
   # If using virtual environment
   source smugdups_env/bin/activate
   python main.py
   ```

2. **Select albums** to scan from the left panel
3. **Click "Scan for Duplicates"** to find duplicates
4. **Review duplicate groups** and select which copies to keep using radio buttons
5. **Click "Move to Review Album"** to move duplicates (working moveimages!)

### Advanced Features

- **Album sorting** by name, photo count, or date
- **Batch selection** with "All" and "None" buttons
- **Skip duplicate groups** you want to leave unchanged
- **Permanent deletion** option for immediate removal
- **GPS coordinate viewing** for location-tagged photos

## 🗺️ Geographic Features (New in v5.1)

### GPS Data Display
- **Basic view**: Compact coordinates like `🗺️ 40.7589,-73.9851`
- **Detailed view**: Full coordinates with altitude: `🗺️ 40.758896°N, 73.985130°W ⛰️ 15m above sea level`
- **Group statistics**: Headers show `X with GPS` for duplicate groups

### Enhanced Quality Scoring
- Photos with GPS coordinates receive +1 quality score
- Helps identify original photos vs processed copies
- Especially useful for travel photography

### Smart Selection Logic
SmugDups now considers GPS data when recommending which duplicate to keep:
- Original photos often retain GPS data better than processed copies
- Location data adds context for decision making
- Distance calculations between duplicate locations

## 🔧 Fixed Issues in v5.1

### Radio Button Selection (FIXED)
- **Problem**: Radio button selection for choosing which duplicate to keep was not working
- **Solution**: Fixed signal/slot connections and QButtonGroup behavior
- **Result**: Users can now properly select which photo to keep in each duplicate group

### Cross-Platform Compatibility
- **Unicode/Emoji handling**: Improved cross-platform emoji support
- **Font families**: Better CSS font handling across different systems
- **Windows compatibility**: Enhanced file handling and path management

## 📦 Project Structure

```
SmugDups/
├── main.py                          # Entry point
├── smugmug_api.py                   # SmugMug API wrapper with OAuth + GPS
├── credentials.py                   # Your API keys (create from template)
├── requirements.txt                 # Python dependencies
├── smugdups_env/                    # Virtual environment (created during setup)
├── core/
│   ├── models.py                    # DuplicatePhoto data model with GPS
│   └── duplicate_finder.py          # Background duplicate detection
├── gui/
│   ├── main_window.py              # Main application window
│   ├── duplicate_widget.py         # Duplicate group management UI with FIXED radio buttons
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
- **GPS data:** Automatic collection when available

## 🔧 Technical Details

### Working MoveImages Implementation
SmugDups v5.1 uses the correct SmugMug API v2 moveimages format:

```python
# Correct moveimages format (discovered through SmugMug support):
url = f"https://api.smugmug.com/api/v2/album/{target_album}!moveimages"
data = {
    'MoveUris': f"/api/v2/album/{source_album}/image/{image_id}-0"
}
```

### GPS Data Collection
SmugDups automatically requests GPS coordinates:

```python
# Enhanced API filter with GPS coordinates
'_filter': 'ImageKey,FileName,ArchivedMD5,ArchivedSize,Date,WebUri,ThumbnailUrl,Title,Caption,Keywords,DateTimeOriginal,Latitude,Longitude,Altitude'
```

### Fixed Radio Button Implementation
The radio button selection issue has been resolved with:

```python
# FIXED: Proper signal handling and state management
radio.setChecked(photo.keep)  # Set state BEFORE connecting signals
self.button_group.addButton(radio, index)  # Add to group
radio.toggled.connect(lambda checked, idx=index: self._on_radio_toggled(checked, idx))
```

### Key Technical Insights
- **Parameter name:** `MoveUris` (not `ImageUris`)
- **URI format:** AlbumImage URI format (`/api/v2/album/SOURCE/image/ID`)
- **Endpoint:** Use target album's moveimages endpoint
- **Verification:** Check source no longer has image and target does
- **GPS handling:** Graceful fallback when coordinates unavailable
- **Radio buttons:** Fixed signal timing and state management

## 🛠️ Troubleshooting

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

**"Radio buttons not working"** (FIXED in v5.1)
- This issue has been resolved in the current version
- Radio button selection now properly updates photo.keep attributes
- Visual feedback shows selected state correctly

**Virtual Environment Issues**
- Ensure virtual environment is activated before running
- Reinstall packages if switching Python versions
- Use `which python` to verify correct Python installation

### Debug Mode
Enable detailed logging by checking console output during operations. You can also use the debug method:

```python
# In duplicate widget, call this method to check radio button state
duplicate_widget.debug_radio_state()
```

## 📈 Performance

- **Scan speed:** ~100 images per second (network dependent)
- **Memory usage:** Minimal (thumbnails cached locally)
- **API compliance:** Rate limited to respect SmugMug guidelines
- **Move verification:** Automatic confirmation of successful operations
- **GPS processing:** No performance impact when coordinates unavailable
- **UI responsiveness:** Fixed radio button selection with immediate feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with your SmugMug account
5. Submit a pull request

### Development Guidelines
- Follow existing code structure
- Add comprehensive error handling
- Test with real SmugMug data including GPS-tagged photos
- Update documentation for new features
- Test radio button functionality across different duplicate scenarios

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SmugMug Support Team** for helping solve the moveimages parameter format
- **SmugMug API Team** for maintaining comprehensive API documentation
- **PyQt6 Community** for excellent GUI framework
- **GPS/Photography Community** for feedback on geographic feature needs

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/xtremetoonz/SmugDups/issues)
- **Discussions:** [GitHub Discussions](https://github.com/xtremetoonz/SmugDups/discussions)
- **Email:** Check GitHub profile for contact information

## 🗺️ Roadmap

### Planned Features
- **Map integration** for visual location display
- **Location-based clustering** of duplicate groups
- **Batch operations** for geographic regions
- **GPX export** for location data
- **Advanced filtering** by GPS availability and location proximity

### Version History
- **v5.1:** GPS coordinate support, enhanced quality scoring, FIXED radio button selection
- **v5.0:** Working moveimages, rebranded to SmugDups
- **v2.x:** Collectimages approach
- **v1.x:** Initial duplicate detection implementation

### Recent Fixes
- **Radio Button Selection**: Fixed QButtonGroup interference and signal timing
- **Cross-platform compatibility**: Improved Unicode handling and Windows support
- **GPS coordinate display**: Enhanced location metadata presentation
- **Quality scoring**: Location data now contributes to duplicate selection logic

---

**SmugDups v5.1** - Making SmugMug duplicate management simple, effective, and location-aware! 🎉🗺️

*"Finally, true moveimages functionality that actually works - now with GPS support and fixed radio button selection!"*

## ⚡ Quick Start Guide

1. **Install Python 3.9+** and clone this repository
2. **Create virtual environment:** `python -m venv smugdups_env`
3. **Activate environment:** `source smugdups_env/bin/activate` (Linux/Mac) or `smugdups_env\Scripts\activate` (Windows)
4. **Install dependencies:** `pip install -r requirements.txt`
5. **Set up credentials:** Copy `credentialsTemplate.py` to `credentials.py` and add your SmugMug API details
6. **Run SmugDups:** `python main.py`
7. **Select albums, scan for duplicates, choose which copies to keep, and move/delete!**

The radio button selection is now working perfectly - you can reliably choose which duplicate photo to keep in each group!
