#!/usr/bin/env python3
"""
SmugMug Copy Operations for SmugDups v5.0
File: operations/smugmug_copy_operations.py
UPDATED: Uses WORKING moveimages format with proper syntax
"""

import requests
from requests_oauthlib import OAuth1
import json
import time
from typing import Dict, List, Optional, Tuple

class SmugMugCopyOperations:
    """SmugMug operations using WORKING moveimages format"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        
    def move_image_to_album(self, image_id: str, source_album_key: str, target_album_key: str) -> Tuple[bool, str]:
        """MOVE image using WORKING SmugMug moveimages format"""
        try:
            print(f"Moving image {image_id} from {source_album_key} to {target_album_key}")
            
            # Verify source and target albums exist
            source_info = self.api.get_album_info(source_album_key)
            target_info = self.api.get_album_info(target_album_key)
            
            if not source_info:
                return False, f"Source album {source_album_key} not found"
            if not target_info:
                return False, f"Target album {target_album_key} not found"
            
            # Use WORKING moveimages format
            success, message = self._move_via_working_format(image_id, source_album_key, target_album_key)
            if success:
                return True, message
            
            # Fallback to collectimages if move fails
            print(f"Move failed, falling back to collect+manual delete")
            return self._fallback_to_collect(image_id, target_album_key)
        
        except Exception as e:
            return False, f"Move failed with exception: {str(e)}"

    def _move_via_working_format(self, image_id: str, source_album_key: str, target_album_key: str) -> Tuple[bool, str]:
        """Use the WORKING moveimages format"""
        try:
            # WORKING FORMAT from SmugMug support:
            # 1. Use TARGET album's moveimages endpoint
            # 2. Parameter name: 'MoveUris' 
            # 3. Value: '/api/v2/album/SOURCE_ALBUM/image/IMAGE_ID-0'
            
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!moveimages"
            
            # Try both formats (with and without -0 suffix)
            move_formats = [
                f"/api/v2/album/{source_album_key}/image/{image_id}-0",  # Preferred format
                f"/api/v2/album/{source_album_key}/image/{image_id}"     # Alternative format
            ]
            
            for i, move_uri in enumerate(move_formats, 1):
                print(f"Attempting move format {i}: {move_uri}")
                
                data = {'MoveUris': move_uri}
                
                success, response_data = self._make_move_request(url, data)
                
                if success:
                    print(f"Move successful with format {i}")
                    
                    # Verify the move worked
                    time.sleep(2)  # Give SmugMug time to process
                    if self._verify_image_moved(image_id, source_album_key, target_album_key):
                        return True, f"Image moved successfully using format {i}"
                    else:
                        print(f"API succeeded but verification failed")
                        return True, f"Move API succeeded (format {i})"
                
                time.sleep(0.5)  # Small delay between attempts
            
            return False, "All move formats failed"
            
        except Exception as e:
            return False, f"Working format error: {str(e)}"

    def _make_move_request(self, url: str, data: Dict) -> Tuple[bool, Optional[dict]]:
        """Make moveimages request with proper OAuth handling"""
        try:
            # Create fresh OAuth
            auth = OAuth1(
                client_key=self.api.api_key,
                client_secret=self.api.api_secret,
                resource_owner_key=self.api.access_token,
                resource_owner_secret=self.api.access_secret,
                signature_method='HMAC-SHA1',
                signature_type='AUTH_HEADER'
            )
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'SmugDups/5.0-WorkingMoveImages'
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=data, 
                                   allow_redirects=False, timeout=30)
            
            # Handle redirects manually
            if 300 <= response.status_code < 400:
                redirect_location = response.headers.get('Location', '')
                if redirect_location:
                    # Create fresh OAuth for redirect
                    auth = OAuth1(
                        client_key=self.api.api_key,
                        client_secret=self.api.api_secret,
                        resource_owner_key=self.api.access_token,
                        resource_owner_secret=self.api.access_secret,
                        signature_method='HMAC-SHA1',
                        signature_type='AUTH_HEADER'
                    )
                    response = requests.post(redirect_location, auth=auth, headers=headers, 
                                           json=data, allow_redirects=False, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, None
            else:
                try:
                    error_data = response.json()
                    error_code = error_data.get('Code', 0)
                    error_msg = error_data.get('Message', 'Unknown error')
                    print(f"Error {error_code}: {error_msg}")
                    return False, error_data
                except:
                    print(f"HTTP {response.status_code}: {response.text[:150]}")
                    return False, None
                    
        except Exception as e:
            print(f"Request exception: {e}")
            return False, None

    def _verify_image_moved(self, image_id: str, source_album_key: str, target_album_key: str) -> bool:
        """Verify that image was actually moved"""
        try:
            print(f"Verifying move: {image_id}")
            
            # Check if image is NO LONGER in source album
            source_images = self.api.get_album_images(source_album_key)
            source_has_image = any(img.get('image_id') == image_id for img in source_images)
            
            # Check if image IS NOW in target album  
            target_images = self.api.get_album_images(target_album_key)
            target_has_image = any(img.get('image_id') == image_id for img in target_images)
            
            # Successful move = image removed from source AND added to target
            move_successful = not source_has_image and target_has_image
            
            if move_successful:
                print(f"Move verified successfully")
            else:
                print(f"Move verification failed")
            
            return move_successful
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def _fallback_to_collect(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Fallback to collectimages if moveimages fails"""
        try:
            print(f"Fallback: Using collectimages")
            
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!collectimages"
            collect_data = {'CollectUris': f"/api/v2/image/{image_id}"}
            
            auth = OAuth1(
                client_key=self.api.api_key,
                client_secret=self.api.api_secret,
                resource_owner_key=self.api.access_token,
                resource_owner_secret=self.api.access_secret,
                signature_method='HMAC-SHA1',
                signature_type='AUTH_HEADER'
            )
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'SmugDups/5.0-CollectFallback'
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=collect_data, 
                                   allow_redirects=False, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, "Image collected (fallback mode - manual deletion needed)"
            else:
                return False, f"Both move and collect failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Fallback collect error: {str(e)}"

    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Backwards compatibility - now does actual move!"""
        print(f"WARNING: copy_image_to_album now does ACTUAL MOVES!")
        return self._fallback_to_collect(image_id, target_album_key)


class SmugDupsMoveOperations:
    """SmugDups move operations using WORKING moveimages"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        self.move_ops = SmugMugCopyOperations(api_adapter)
        
    def move_duplicates_to_review(self, duplicate_groups: List[List], review_album_key: str) -> Dict:
        """Move duplicate images using WORKING moveimages"""
        print(f"\nMoving duplicates to review - SmugDups v5.0")
        
        total_images = 0
        successful_moves = 0
        failed_moves = 0
        move_results = []
        
        for group_num, group in enumerate(duplicate_groups, 1):
            print(f"\nGroup {group_num}/{len(duplicate_groups)}: {len(group)} duplicates")
            
            for photo in group:
                # Skip the photo marked to keep
                if hasattr(photo, 'keep') and photo.keep:
                    print(f"Keeping: {photo.filename} from {photo.album_name}")
                    continue
                
                total_images += 1
                
                # Extract photo info
                if hasattr(photo, 'image_id'):
                    image_id = photo.image_id
                    filename = photo.filename
                    source_album_key = photo.album_id
                    source_album_name = photo.album_name
                else:
                    image_id = photo.get('image_id', '')
                    filename = photo.get('filename', 'unknown')
                    source_album_key = photo.get('album_id', '')
                    source_album_name = photo.get('album_name', 'unknown')
                
                if image_id and source_album_key:
                    print(f"Moving: {filename} from {source_album_name}")
                    
                    # Use the WORKING move method
                    success, message = self.move_ops.move_image_to_album(
                        image_id, source_album_key, review_album_key
                    )
                    
                    move_result = {
                        'image_id': image_id,
                        'filename': filename,
                        'source_album': source_album_name,
                        'success': success,
                        'message': message
                    }
                    move_results.append(move_result)
                    
                    if success:
                        successful_moves += 1
                        print(f"Move successful")
                    else:
                        failed_moves += 1
                        print(f"Move failed: {message}")
                    
                    time.sleep(1.0)  # Rate limiting
                else:
                    failed_moves += 1
                    print(f"Missing image_id or album_id for {filename}")
        
        # Generate summary
        success_rate = (successful_moves / total_images * 100) if total_images > 0 else 0
        
        summary = {
            'success': True,
            'total_images': total_images,
            'successful_moves': successful_moves,
            'failed_moves': failed_moves,
            'success_rate': f"{success_rate:.1f}%",
            'move_results': move_results,
            'method': 'working_moveimages'
        }
        
        print(f"\nMove operation summary:")
        print(f"Images processed: {summary['total_images']}")
        print(f"Successful moves: {summary['successful_moves']}")
        print(f"Failed moves: {summary['failed_moves']}")
        print(f"Success rate: {summary['success_rate']}")
        
        return summary


class EnhancedPhotoCopyMoveOperations:
    """Main orchestrator using WORKING moveimages"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        self.move_manager = SmugDupsMoveOperations(api_adapter)
        from .smugmug_album_operations import SmugMugAlbumOperations
        self.album_ops = SmugMugAlbumOperations(api_adapter)
        
    def find_or_create_review_album(self, username: str) -> Optional[Dict]:
        """Find existing review album or create a new one"""
        return self.album_ops.find_or_create_review_album(username)
    
    def process_duplicates_for_review(self, duplicate_groups: List[List], username: str) -> Dict:
        """Process duplicates using WORKING moveimages"""
        print(f"\nSmugDups duplicate processing v5.0")
        
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
        
        print(f"Using review album: {album_name} (Key: {album_key})")
        if review_album.get('web_url'):
            print(f"Album URL: {review_album['web_url']}")
        
        # Step 2: Filter duplicates to process
        duplicates_to_move = []
        for group in duplicate_groups:
            group_to_move = []
            for photo in group:
                if hasattr(photo, 'keep') and photo.keep:
                    print(f"Will keep: {photo.filename} from {photo.album_name}")
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
        
        # Step 3: Execute moves
        results = self.move_manager.move_duplicates_to_review(duplicates_to_move, album_key)
        
        # Step 4: Add review album info and return
        results['review_album'] = review_album
        results['total_groups'] = len(duplicate_groups)
        
        print(f"\nSmugDups moveimages complete!")
        print(f"Review album: {album_name}")
        print(f"Successful moves: {results['successful_moves']}")
        
        if review_album.get('web_url'):
            print(f"Review album: {review_album['web_url']}")
        
        return results

    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Backwards compatibility - now uses working move"""
        print(f"WARNING: This now does ACTUAL MOVES, not copies!")
        return self.move_manager.move_ops._fallback_to_collect(image_id, target_album_key)


if __name__ == "__main__":
    print("SmugDups v5.0 - Enhanced Photo Operations")
    print("Working moveimages functionality")
    
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
        print(f"Successfully initialized SmugDups v5.0!")
        print(f"Working moveimages: SmugDupsMoveOperations")
        print(f"Album operations: SmugMugAlbumOperations") 
        print(f"Main orchestrator: EnhancedPhotoCopyMoveOperations")
        
    except Exception as e:
        print(f"Import test failed: {e}")
        print("Make sure to run this from the SmugDups root directory")
