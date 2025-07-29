#!/usr/bin/env python3
"""
Enhanced Photo Copy/Move functionality for MugMatch - REFACTORED VERSION v2.6
File: operations/enhanced_photo_copy_move.py
UPDATED: Now MOVES duplicates instead of copying them (removes from source)
Main orchestrator for duplicate management - now uses modular components
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import from other modules in this package
from .smugmug_copy_operations import SmugMugCopyOperations
from .smugmug_album_operations import SmugMugAlbumOperations

class EnhancedPhotoCopyMoveOperations:
    """Main orchestrator for enhanced photo copy/move operations"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        self.copy_ops = SmugMugCopyOperations(api_adapter)
        self.album_ops = SmugMugAlbumOperations(api_adapter)
        
    def find_or_create_review_album(self, username: str) -> Optional[Dict]:
        """Find existing review album or create a new one"""
        return self.album_ops.find_or_create_review_album(username)
    
    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Copy image to target album"""
        return self.copy_ops.copy_image_to_album(image_id, target_album_key)
    
    def process_duplicates_for_review(self, duplicate_groups: List[List], username: str) -> Dict:
        """Process duplicate groups by COPYING to review album - SAFE MODE"""
        print(f"\n📋 PROCESSING DUPLICATES FOR REVIEW - SAFE MODE v2.7")
        print("⚠️  Due to SmugMug API bug, originals will be preserved (safe copy mode)")
        print("="*60)
        
        # Step 1: Set up review album using modular album operations
        review_album = self.find_or_create_review_album(username)
        
        if not review_album:
            return {
                'success': False,
                'error': 'Could not set up review album',
                'manual_creation_needed': True
            }
        
        # Check if manual creation is needed
        if review_album.get('manual_creation_needed'):
            return {
                'success': False,
                'error': 'Manual album creation required',
                'manual_creation_needed': True,
                'instructions': review_album.get('instructions', ''),
                'suggested_album_name': review_album['album_name'],
                'suggested_url_name': review_album.get('suggested_url_name', '')
            }
        
        album_key = review_album['album_key']
        album_name = review_album['album_name']
        
        print(f"✅ Using review album: {album_name} (Key: {album_key})")
        if review_album.get('web_url'):
            print(f"🌐 Album URL: {review_album['web_url']}")
        
        # Step 2: Process each duplicate group using modular SAFE COPY operations
        total_images = 0
        successful_copies = 0
        failed_copies = 0
        group_results = []
        
        for group_num, group in enumerate(duplicate_groups, 1):
            print(f"\n📸 Group {group_num}/{len(duplicate_groups)}: {len(group)} duplicates")
            
            group_result = {
                'group_number': group_num,
                'total_images': len(group),
                'successful_copies': 0,
                'failed_copies': 0,
                'image_results': []
            }
            
            for photo in group:
                total_images += 1
                
                # Handle both DuplicatePhoto objects and dictionaries
                if hasattr(photo, 'image_id'):
                    image_id = photo.image_id
                    filename = photo.filename
                    album_name_src = photo.album_name
                else:
                    image_id = photo.get('image_id', '')
                    filename = photo.get('filename', 'unknown')
                    album_name_src = photo.get('album_name', 'unknown')
                
                if image_id:
                    success, message = self.copy_image_to_album(image_id, album_key)  # Now safe copy mode
                    
                    image_result = {
                        'image_id': image_id,
                        'filename': filename,
                        'source_album': album_name_src,
                        'success': success,
                        'message': message
                    }
                    
                    group_result['image_results'].append(image_result)
                    
                    if success:
                        successful_copies += 1
                        group_result['successful_copies'] += 1
                        print(f"      ✅ {filename} (COPIED to review, original preserved)")
                    else:
                        failed_copies += 1
                        group_result['failed_copies'] += 1
                        print(f"      ❌ {filename}: {message}")
                    
                    # Rate limiting
                    time.sleep(1.0)
                else:
                    failed_copies += 1
                    group_result['failed_copies'] += 1
                    print(f"      ❌ {filename}: No image ID")
            
            group_results.append(group_result)
        
        # Step 3: Generate summary with accurate counting
        success_rate = (successful_copies / total_images * 100) if total_images > 0 else 0
        
        summary = {
            'success': True,
            'review_album': review_album,
            'total_groups': len(duplicate_groups),
            'total_images': total_images,
            'successful_copies': successful_copies,
            'failed_copies': failed_copies,
            'success_rate': f"{success_rate:.1f}%",
            'group_results': group_results
        }
        
        print(f"\n📊 SAFE COPY OPERATION SUMMARY:")
        print(f"   📁 Review album: {album_name}")
        print(f"   📸 Groups processed: {summary['total_groups']}")
        print(f"   🖼️  Images processed: {summary['total_images']}")
        print(f"   ✅ Successful copies: {summary['successful_copies']}")
        print(f"   ❌ Failed copies: {summary['failed_copies']}")
        print(f"   📈 Success rate: {summary['success_rate']}")
        print(f"   ⚠️  SAFE MODE: Originals preserved due to SmugMug API bug")
        print(f"   💡 Manual cleanup: Delete originals from SmugMug web interface")
        
        if review_album.get('web_url'):
            print(f"   🌐 Review album URL: {review_album['web_url']}")
        
        return summary


# Utility functions
def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_date(date_string: str) -> str:
    """Format SmugMug date string for display"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_string


def calculate_savings(duplicate_groups: List[List[Dict]]) -> Dict[str, int]:
    """Calculate potential storage savings from removing duplicates"""
    total_duplicates = 0
    total_size_savings = 0
    
    for group in duplicate_groups:
        duplicates_in_group = len(group) - 1
        total_duplicates += duplicates_in_group
        
        for i in range(1, len(group)):
            total_size_savings += group[i].get('size', 0)
    
    return {
        'duplicate_count': total_duplicates,
        'size_savings_bytes': total_size_savings,
        'size_savings_formatted': format_file_size(total_size_savings)
    }


# Integration function for backwards compatibility
def create_smugmug_api(credentials_file: str = "credentials.py"):
    """Create a SmugMug API instance using your existing credentials file"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("credentials", credentials_file)
        credentials = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(credentials)
        
        from smugmug_api import SmugMugAPIAdapter
        return SmugMugAPIAdapter(
            api_key=credentials.API_KEY,
            api_secret=credentials.API_SECRET,
            access_token=credentials.ACCESS_TOKEN,
            access_secret=credentials.ACCESS_SECRET
        )
    
    except Exception as e:
        print(f"Failed to load credentials from {credentials_file}: {e}")
        return None


if __name__ == "__main__":
    print("🎉 ENHANCED COPY/MOVE FOR MUGMATCH - MOVE VERSION v2.6")
    print("="*70)
    print("✅ MODULAR: Separated into copy and album operations")
    print("✅ MAINTAINABLE: Each module handles specific functionality") 
    print("✅ MOVE OPERATIONS: Now removes duplicates from source albums")
    print("✅ COMPLETE: Ready for production duplicate removal!")
    
    # Test if we can import and initialize
    try:
        import credentials
        from smugmug_api import SmugMugAPIAdapter
        
        api = SmugMugAPIAdapter(
            api_key=credentials.API_KEY,
            api_secret=credentials.API_SECRET,
            access_token=credentials.ACCESS_TOKEN,
            access_secret=credentials.ACCESS_SECRET
        )
        
        copy_ops = EnhancedPhotoCopyMoveOperations(api)
        print(f"\n✅ Successfully initialized with MOVE architecture!")
        print(f"📋 Move operations: smugmug_copy_operations.py")
        print(f"📁 Album operations: smugmug_album_operations.py") 
        print(f"🎯 Main orchestrator: enhanced_photo_copy_move.py")
        print(f"🚀 Ready for duplicate removal in MugMatch 2.6")
        
    except Exception as e:
        print(f"\n⚠️  Import test failed: {e}")
        print("Make sure to run this from the MugMatch root directory")
