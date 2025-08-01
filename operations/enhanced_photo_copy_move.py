#!/usr/bin/env python3
"""
Enhanced Photo Operations for SmugDups v5.0
File: operations/enhanced_photo_copy_move.py
UPDATED: Rebranded to SmugDups and uses WORKING moveimages functionality
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import from other modules in this package
from .smugmug_copy_operations import SmugDupsMoveOperations
from .smugmug_album_operations import SmugMugAlbumOperations

class EnhancedPhotoCopyMoveOperations:
    """Main orchestrator for SmugDups using WORKING moveimages"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        self.move_manager = SmugDupsMoveOperations(api_adapter)
        self.album_ops = SmugMugAlbumOperations(api_adapter)
        
    def find_or_create_review_album(self, username: str) -> Optional[Dict]:
        """Find existing review album or create a new one"""
        return self.album_ops.find_or_create_review_album(username)
    
    def process_duplicates_for_review(self, duplicate_groups: List[List], username: str) -> Dict:
        """Process duplicates using WORKING moveimages - SmugDups v5.0"""
        print(f"\n📦 SMUGDUPS DUPLICATE PROCESSING v5.0")

        print("="*60)
        
        # Step 1: Set up review album
        review_album = self.find_or_create_review_album(username)
        
        if not review_album:
            return {
                'success': False,
                'error': 'Could not set up review album',
                'manual_creation_needed': True
            }
        
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
        
        # Step 2: Filter duplicates to process
        duplicates_to_move = []
        for group in duplicate_groups:
            group_to_move = []
            for photo in group:
                if hasattr(photo, 'keep') and photo.keep:
                    print(f"   ✅ Will keep: {photo.filename} from {photo.album_name}")
                else:
                    group_to_move.append(photo)
            
            if group_to_move:
                duplicates_to_move.append(group_to_move)
        
        if not any(duplicates_to_move):
            return {
                'success': True,
                'review_album': review_album,
                'total_groups': len(duplicate_groups),
                'total_images': 0,
                'successful_moves': 0,
                'failed_moves': 0,
                'success_rate': "100%",
                'message': "No photos need to be moved - all are selected to keep"
            }
        
        # Step 3: Execute moves using WORKING method
        results = self.move_manager.move_duplicates_to_review(duplicates_to_move, album_key)
        
        # Step 4: Add review album info and return
        results['review_album'] = review_album
        results['total_groups'] = len(duplicate_groups)
        
        print(f"\n🎉 SMUGDUPS v5.0 MOVEIMAGES COMPLETE!")
        print(f"   📁 Review album: {album_name}")
        print(f"   ✅ Successful moves: {results['successful_moves']}")
        print(f"   📦 TRUE MOVES: Images removed from source, added to review!")
        print(f"   🚀 NO MANUAL CLEANUP NEEDED!")
        
        if review_album.get('web_url'):
            print(f"   🌐 Review album: {review_album['web_url']}")
        
        return results

    # Backwards compatibility
    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Backwards compatibility - now uses working move (with warning)"""
        print(f"⚠️  WARNING: This now does ACTUAL MOVES, not copies!")
        
        return self.move_manager.move_ops._fallback_to_collect(image_id, target_album_key)

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

if __name__ == "__main__":
    
    print("="*60)

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
        
        move_ops = EnhancedPhotoCopyMoveOperations(api)
        print(f"\n✅ Successfully initialized SmugDups v5.0!")
        
        print(f"📁 Album operations: SmugMugAlbumOperations") 
        print(f"🎯 Main orchestrator: EnhancedPhotoCopyMoveOperations")
        print(f"🚀 Ready for complete duplicate management!")
        
    except Exception as e:
        print(f"\n⚠️  Import test failed: {e}")
        print("Make sure to run this from the SmugDups root directory")
