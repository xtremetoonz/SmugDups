#!/usr/bin/env python3
"""
SmugMug Copy Operations - Core copying functionality v2.6
File: operations/smugmug_copy_operations.py
UPDATED: Now uses MOVE operations to actually remove duplicates from source albums
Contains the core image moving methods separated from album management
"""

import requests
from requests_oauthlib import OAuth1
import json
import time
from typing import Dict, List, Optional, Tuple

class SmugMugCopyOperations:
    """Core SmugMug image moving operations (was copy, now move)"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        
    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """COPY image to target album - SAFE MODE (no delete due to SmugMug bug)"""
        try:
            print(f"   📋 COPYING image {image_id} to album {target_album_key} (SAFE MODE)")
            print(f"   ⚠️  NOTE: Original will remain due to SmugMug delete bug")
            
            # First, verify the image and album exist
            print(f"   🔍 Verifying image and album exist...")
            
            # Check if image exists and get its details
            image_details = self.api.get_image_details(image_id)
            if not image_details:
                return False, f"Image {image_id} not found or not accessible"
            
            print(f"   ✅ Image verified: {image_details.get('FileName', 'Unknown')}")
            
            # Check if album exists and get its details
            album_info = self.api.get_album_info(target_album_key)
            if not album_info:
                return False, f"Album {target_album_key} not found or not accessible"
            
            print(f"   ✅ Album verified: {album_info.get('name', 'Unknown')}")
        
            # SAFE MODE: Only copy, don't delete (due to SmugMug bug)
            success, message = self._safe_copy_only(image_id, target_album_key, image_details)
            if success:
                return True, message
        
            # Fallback: Manual instructions
            debug_info = self._debug_api_response(image_id, target_album_key)
            return self._provide_enhanced_manual_instructions(image_id, target_album_key, debug_info)
        
        except Exception as e:
            return False, f"Copy failed with exception: {str(e)}"

    def _safe_copy_only(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """SAFE copy that doesn't delete original (due to SmugMug bug)"""
        try:
            print(f"   🔄 Safe copy-only approach (no delete)")
            
            # Step 1: Copy using the working collect method
            success, message = self._copy_via_collect_multiple_formats(image_id, target_album_key, image_details)
            if not success:
                return False, f"Copy step failed: {message}"
            
            print(f"   ✅ Copy API call successful, now verifying...")
            
            # Step 2: Verify the image actually appeared in the target album
            time.sleep(2)  # Give SmugMug time to process
            
            if not self._verify_image_in_album(image_id, target_album_key):
                print(f"   ❌ VERIFICATION FAILED: Image not found in target album despite 200 OK!")
                return False, "Copy appeared successful but image not found in destination album"
            
            print(f"   ✅ Copy verified - image confirmed in target album")
            print(f"   ℹ️  SAFE MODE: Original image kept in source album (SmugMug delete bug)")
            print(f"   💡 You can manually delete originals later from SmugMug web interface")
            
            return True, f"Image safely copied to review album (original preserved due to SmugMug API bug)"
                
        except Exception as e:
            return False, f"Safe copy error: {str(e)}"

    def _move_via_moveimages_quick_test(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """Quick test of moveimages endpoint - only try most likely formats"""
        try:
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!moveimages"
            print(f"   🔍 Quick MOVE test: {url}")
            
            # Only try the most promising formats to save time
            quick_tests = [
                {'ImageUris': f"/api/v2/image/{image_id}"},           # String format
                {'ImageUris': f"/api/v2/image/{image_id}-0"},         # Redirect string format
                {'ImageUris': [f"/api/v2/image/{image_id}"]},         # Array format
            ]
            
            for i, move_data in enumerate(quick_tests):
                print(f"     📋 Quick test {i+1}: {move_data}")
                
                success, response_data = self._make_move_request(url, move_data)
                
                if success:
                    print(f"   ✅ SUCCESS with moveimages quick test {i+1}!")
                    return True, f"Image MOVED via moveimages quick test {i+1}"
                
                time.sleep(0.1)  # Very short delay
            
            print(f"   ❌ All moveimages quick tests failed")
            return False, "moveimages quick tests failed"
            
        except Exception as e:
            print(f"   💥 Move quick test exception: {e}")
            return False, f"Move quick test error: {str(e)}"

    def _move_via_moveimages_multiple_formats(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """Try SmugMug's moveimages endpoint with multiple URI and data formats"""
        try:
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!moveimages"
            print(f"   🔍 MOVE METHOD: {url}")
            
            # Build URI candidates
            image_uri_formats = [
                f"/api/v2/image/{image_id}",                    # Standard format
                f"/api/v2/image/{image_id}-0",                  # Redirect format
                image_details.get('Uri', ''),                   # URI from image details
                image_details.get('Uris', {}).get('Image', ''), # Alternative URI location
            ]
            
            # Filter empty URIs and add full URL versions
            clean_uris = [uri for uri in image_uri_formats if uri]
            full_url_formats = [f"https://api.smugmug.com{uri}" for uri in clean_uris if uri.startswith('/')]
            all_uri_formats = clean_uris + full_url_formats
            
            for i, image_uri in enumerate(all_uri_formats):
                print(f"   📤 Trying URI format {i+1}: {image_uri}")
                
                # Try multiple data formats for move operations
                data_formats = [
                    {'ImageUris': [image_uri]},             # Array format
                    {'ImageUris': image_uri},               # String format  
                    {'MoveUris': [image_uri]},              # Alternative parameter name
                    {'MoveUris': image_uri},                # Alternative parameter as string
                ]
                
                for j, move_data in enumerate(data_formats):
                    print(f"     📋 Data format {j+1}: {move_data}")
                    
                    success, response_data = self._make_move_request(url, move_data)
                    
                    if success:
                        print(f"   ✅ SUCCESS with MOVE URI format {i+1}, data format {j+1}!")
                        return True, f"Image MOVED via moveimages URI format {i+1}, data format {j+1}"
                    
                    # Check for specific error handling
                    if response_data and isinstance(response_data, dict):
                        if self._handle_move_error(response_data):
                            continue  # Try next format
                        
                        # Check for fatal errors
                        code = response_data.get('Code', 0)
                        if code in [4, 5, 15]:  # Invalid album, image, or permission denied
                            message = response_data.get('Message', 'Unknown error')
                            return False, f"Fatal error (Code {code}): {message}"
                    
                    time.sleep(0.2)  # Small delay between attempts
                
                time.sleep(0.5)  # Delay between URI attempts
            
            return False, f"All {len(all_uri_formats)} MOVE URI formats failed"
            
        except Exception as e:
            print(f"   💥 Move method exception: {e}")
            return False, f"Move method error: {str(e)}"

    def _copy_then_delete_original(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """Fallback: Copy to review album then delete from original location - WITH VERIFICATION"""
        try:
            print(f"   🔄 Fallback: Copy then delete approach")
            
            # Step 1: Copy using the working collect method
            success, message = self._copy_via_collect_multiple_formats(image_id, target_album_key, image_details)
            if not success:
                return False, f"Copy step failed: {message}"
            
            print(f"   ✅ Copy API call successful, now verifying...")
            
            # Step 1.5: CRITICAL - Verify the image actually appeared in the target album
            time.sleep(2)  # Give SmugMug time to process
            
            if not self._verify_image_in_album(image_id, target_album_key):
                print(f"   ❌ VERIFICATION FAILED: Image not found in target album despite 200 OK!")
                return False, "Copy appeared successful but image not found in destination album"
            
            print(f"   ✅ Copy verified - image confirmed in target album")
            
            # Step 2: Delete the original image
            print(f"   🗑️ Now deleting original from source album...")
            success, delete_message = self.api.delete_image_with_details(image_id)
            if success:
                print(f"   ✅ Original image deleted successfully!")
                
                # Step 3: FINAL VERIFICATION - Check if image is still in target album after delete
                print(f"   🔍 Final verification: Checking if image still in target album after delete...")
                time.sleep(2)  # Give SmugMug time to process delete
                
                if self._verify_image_in_album(image_id, target_album_key):
                    print(f"   ✅ FINAL SUCCESS: Image confirmed in target album after delete operation")
                    return True, f"Image moved via verified copy+delete: {message}"
                else:
                    print(f"   ❌ CRITICAL ISSUE: Image disappeared from target album after delete!")
                    print(f"   🚨 The delete operation may have affected the target album too!")
                    return False, "Image disappeared from target album after delete - possible SmugMug bug"
            else:
                print(f"   ⚠️  Copy succeeded but delete failed: {delete_message}")
                print(f"   ⚠️  WARNING: Image now exists in BOTH albums!")
                return True, f"Image copied but original delete failed: {delete_message}"
                
        except Exception as e:
            return False, f"Copy+delete error: {str(e)}"

    def _verify_image_in_album(self, image_id: str, target_album_key: str) -> bool:
        """Verify that an image actually exists in the target album - ENHANCED DEBUG"""
        try:
            print(f"      🔍 Verifying image {image_id} in album {target_album_key}...")
            
            # Get all images in the target album
            album_images = self.api.get_album_images(target_album_key)
            
            if not album_images:
                print(f"      ❌ Could not retrieve album images for verification")
                return False
            
            print(f"      📊 Target album contains {len(album_images)} images")
            
            # ENHANCED: Show ALL images in the album for debugging
            print(f"      🔍 DETAILED album contents:")
            for i, album_image in enumerate(album_images):
                img_id = album_image.get('image_id', 'unknown')
                filename = album_image.get('filename', 'unknown')
                album_name = album_image.get('album_name', 'unknown')
                url = album_image.get('url', 'no-url')
                print(f"         {i+1}. ID: {img_id}, File: {filename}, Album: {album_name}")
                print(f"            URL: {url}")
                
                # Check if this is our image
                if img_id == image_id:
                    print(f"      ✅ FOUND: Image {image_id} confirmed in target album!")
                    print(f"               Filename: {filename}")
                    print(f"               URL: {url}")
                    return True
            
            print(f"      ❌ Image {image_id} NOT found in target album")
            print(f"      🎯 Looking for image ID: {image_id}")
            
            # Also get the album info to double-check we're looking at the right album
            album_info = self.api.get_album_info(target_album_key)
            if album_info:
                print(f"      📁 Album info: {album_info.get('name', 'unknown')} (ID: {album_info.get('id', 'unknown')})")
                print(f"      🌐 Album URL: {album_info.get('url', 'no-url')}")
            
            return False
            
        except Exception as e:
            print(f"      💥 Verification error: {e}")
            import traceback
            traceback.print_exc()
            return False  # Fail safe - assume it didn't work if we can't verify

    def _copy_via_collect_multiple_formats(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """Copy using SmugMug's collectimages with multiple URI and data formats (for copy+delete fallback)"""
        try:
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!collectimages"
            print(f"   🔍 COLLECT METHOD: {url}")
            
            # Build URI candidates
            image_uri_formats = [
                f"/api/v2/image/{image_id}",                    # Standard format
                f"/api/v2/image/{image_id}-0",                  # Redirect format
                image_details.get('Uri', ''),                   # URI from image details
                image_details.get('Uris', {}).get('Image', ''), # Alternative URI location
            ]
            
            # Filter empty URIs and add full URL versions
            clean_uris = [uri for uri in image_uri_formats if uri]
            full_url_formats = [f"https://api.smugmug.com{uri}" for uri in clean_uris if uri.startswith('/')]
            all_uri_formats = clean_uris + full_url_formats
            
            for i, image_uri in enumerate(all_uri_formats):
                print(f"   📤 Trying URI format {i+1}: {image_uri}")
                
                # Use the working string format we discovered
                collect_data = {'CollectUris': image_uri}  # String format that worked
                
                print(f"     📋 Using working string format: {collect_data}")
                
                success, response_data = self._make_collect_request(url, collect_data)
                
                if success:
                    print(f"   ✅ SUCCESS with collect URI format {i+1}!")
                    return True, f"Image copied via CollectUris format {i+1}"
                
                time.sleep(0.2)  # Small delay between attempts
            
            return False, f"All {len(all_uri_formats)} collect URI formats failed"
            
        except Exception as e:
            print(f"   💥 Collect method exception: {e}")
            return False, f"Collect method error: {str(e)}"

    def _make_move_request(self, url: str, move_data: dict) -> Tuple[bool, Optional[dict]]:
        """Make a single move request with fresh OAuth"""
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
                'User-Agent': 'MugMatch/2.6-Move'
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=move_data, 
                                   allow_redirects=False, timeout=30)
            
            print(f"     📥 Response: {response.status_code} - {response.reason}")
            
            # Check for success
            if response.status_code in [200, 201]:
                return True, None
            
            # Try to parse response
            try:
                response_data = response.json()
                
                # Check for success in response data
                if 'Response' in response_data and response_data.get('Code', 0) != 400:
                    print(f"     ✅ SUCCESS detected in response data!")
                    return True, response_data
                
                return False, response_data
                
            except json.JSONDecodeError:
                print(f"     ❌ Non-JSON response: {response.text[:200]}")
                return False, None
                
        except Exception as e:
            print(f"     💥 Request exception: {e}")
            return False, None

    def _make_collect_request(self, url: str, collect_data: dict) -> Tuple[bool, Optional[dict]]:
        """Make a single collect request with fresh OAuth"""
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
                'User-Agent': 'MugMatch/2.6-Collect'
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=collect_data, 
                                   allow_redirects=False, timeout=30)
            
            print(f"     📥 Response: {response.status_code} - {response.reason}")
            
            # Check for success
            if response.status_code in [200, 201]:
                return True, None
            
            # Try to parse response
            try:
                response_data = response.json()
                
                # Check for success in response data
                if 'Response' in response_data and response_data.get('Code', 0) != 400:
                    print(f"     ✅ SUCCESS detected in response data!")
                    return True, response_data
                
                return False, response_data
                
            except json.JSONDecodeError:
                print(f"     ❌ Non-JSON response: {response.text[:200]}")
                return False, None
                
        except Exception as e:
            print(f"     💥 Request exception: {e}")
            return False, None

    def _handle_move_error(self, response_data: dict) -> bool:
        """Handle move error responses. Returns True if we should continue trying other formats."""
        try:
            code = response_data.get('Code', 0)
            message = response_data.get('Message', 'Unknown error')
            
            print(f"       🔍 Error Code: {code} - {message}")
            
            # Continue trying for these errors
            continue_errors = [400]  # Bad Request - might work with different format
            
            # Stop trying for these errors
            fatal_errors = [4, 5, 15, 401, 403, 404]  # Invalid album/image, permission denied, not found
            
            if code in fatal_errors:
                print(f"       ⛔ Fatal error - stopping attempts")
                return False
            elif code in continue_errors:
                print(f"       🔄 Retryable error - continuing with next format")
                return True
            else:
                print(f"       ❓ Unknown error code - continuing")
                return True
                
        except Exception as e:
            print(f"       💥 Error handling exception: {e}")
            return True

    def _debug_api_response(self, image_id: str, target_album_key: str) -> dict:
        """Debug API responses to understand what's wrong"""
        debug_info = {
            'image_id': image_id,
            'album_key': target_album_key,
            'image_access': None,
            'album_access': None
        }
        
        try:
            # Test basic image access
            image_url = f"https://api.smugmug.com/api/v2/image/{image_id}"
            auth = OAuth1(
                client_key=self.api.api_key,
                client_secret=self.api.api_secret,
                resource_owner_key=self.api.access_token,
                resource_owner_secret=self.api.access_secret,
                signature_method='HMAC-SHA1',
                signature_type='AUTH_HEADER'
            )
            
            print(f"   🔍 DEBUG: Testing image access: {image_url}")
            response = requests.get(image_url, auth=auth, allow_redirects=False, timeout=10)
            debug_info['image_access'] = {
                'status': response.status_code,
                'accessible': response.status_code in [200, 301, 302]
            }
            print(f"   🔍 Image access result: {response.status_code}")
            
            # Test basic album access
            album_url = f"https://api.smugmug.com/api/v2/album/{target_album_key}"
            print(f"   🔍 DEBUG: Testing album access: {album_url}")
            response = requests.get(album_url, auth=auth, allow_redirects=False, timeout=10)
            debug_info['album_access'] = {
                'status': response.status_code,
                'accessible': response.status_code in [200, 301, 302]
            }
            print(f"   🔍 Album access result: {response.status_code}")
            
        except Exception as e:
            debug_info['debug_error'] = str(e)
            print(f"   ❌ Debug failed: {e}")
        
        return debug_info

    def _provide_enhanced_manual_instructions(self, image_id: str, target_album_key: str, debug_info: dict) -> Tuple[bool, str]:
        """Provide enhanced manual instructions with debug information"""
        try:
            image_details = self.api.get_image_details(image_id)
            album_info = self.api.get_album_info(target_album_key)
            
            image_name = image_details.get('FileName', f'Image {image_id}') if image_details else f'Image {image_id}'
            album_name = album_info.get('name', 'Review Album') if album_info else 'Review Album'
            
            manual_msg = f"All API MOVE methods failed - Manual move needed: {image_name} → {album_name}"
            
            print(f"   💡 {manual_msg}")
            print(f"      Image ID: {image_id}")
            print(f"      Target Album: {target_album_key}")
            print(f"      Debug info: {debug_info}")
            print(f"      💡 Use SmugMug's 'Collect' feature to manually MOVE this image")
            print(f"      🔍 Consider checking album permissions and image accessibility")
            
            return False, manual_msg
            
        except Exception as e:
            return False, f"Could not generate enhanced manual instructions: {str(e)}"

    def _copy_via_collect_multiple_formats(self, image_id: str, target_album_key: str, image_details: dict) -> Tuple[bool, str]:
        """Try SmugMug's collectimages with multiple URI and data formats"""
        try:
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!collectimages"
            print(f"   🔍 COLLECT METHOD: {url}")
            
            # Build URI candidates
            image_uri_formats = [
                f"/api/v2/image/{image_id}",                    # Standard format
                f"/api/v2/image/{image_id}-0",                  # Redirect format
                image_details.get('Uri', ''),                   # URI from image details
                image_details.get('Uris', {}).get('Image', ''), # Alternative URI location
            ]
            
            # Filter empty URIs and add full URL versions
            clean_uris = [uri for uri in image_uri_formats if uri]
            full_url_formats = [f"https://api.smugmug.com{uri}" for uri in clean_uris if uri.startswith('/')]
            all_uri_formats = clean_uris + full_url_formats
            
            for i, image_uri in enumerate(all_uri_formats):
                print(f"   📤 Trying URI format {i+1}: {image_uri}")
                
                # Try multiple data formats for CollectUris
                data_formats = [
                    {'CollectUris': [image_uri]},           # Array format
                    {'CollectUris': image_uri},             # String format  
                    {'CollectUris': f"{image_uri}"},        # Explicit string format
                ]
                
                for j, collect_data in enumerate(data_formats):
                    print(f"     📋 Data format {j+1}: {collect_data}")
                    
                    success, response_data = self._make_collect_request(url, collect_data)
                    
                    if success:
                        print(f"   ✅ SUCCESS with URI format {i+1}, data format {j+1}!")
                        return True, f"Image copied via CollectUris URI format {i+1}, data format {j+1}"
                    
                    # Check for specific error handling
                    if response_data and isinstance(response_data, dict):
                        if self._handle_collect_error(response_data):
                            continue  # Try next format
                        
                        # Check for fatal errors
                        code = response_data.get('Code', 0)
                        if code in [4, 5, 15]:  # Invalid album, image, or permission denied
                            message = response_data.get('Message', 'Unknown error')
                            return False, f"Fatal error (Code {code}): {message}"
                    
                    time.sleep(0.2)  # Small delay between attempts
                
                time.sleep(0.5)  # Delay between URI attempts
            
            return False, f"All {len(all_uri_formats)} URI formats failed"
            
        except Exception as e:
            print(f"   💥 Collect method exception: {e}")
            return False, f"Collect method error: {str(e)}"

    def _make_collect_request(self, url: str, collect_data: dict) -> Tuple[bool, Optional[dict]]:
        """Make a single collect request with fresh OAuth"""
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
                'User-Agent': 'MugMatch/2.5-Collect'
            }
            
            response = requests.post(url, auth=auth, headers=headers, json=collect_data, 
                                   allow_redirects=False, timeout=30)
            
            print(f"     📥 Response: {response.status_code} - {response.reason}")
            
            # Check for success
            if response.status_code in [200, 201]:
                return True, None
            
            # Try to parse response
            try:
                response_data = response.json()
                
                # Check for success in response data
                if 'Response' in response_data and response_data.get('Code', 0) != 400:
                    print(f"     ✅ SUCCESS detected in response data!")
                    return True, response_data
                
                return False, response_data
                
            except json.JSONDecodeError:
                print(f"     ❌ Non-JSON response: {response.text[:200]}")
                return False, None
                
        except Exception as e:
            print(f"     💥 Request exception: {e}")
            return False, None

    def _handle_collect_error(self, response_data: dict) -> bool:
        """Handle collect error responses. Returns True if we should continue trying other formats."""
        try:
            code = response_data.get('Code', 0)
            message = response_data.get('Message', 'Unknown error')
            
            print(f"       🔍 Error Code: {code} - {message}")
            
            # Continue trying for these errors
            continue_errors = [400]  # Bad Request - might work with different format
            
            # Stop trying for these errors
            fatal_errors = [4, 5, 15, 401, 403, 404]  # Invalid album/image, permission denied, not found
            
            if code in fatal_errors:
                print(f"       ⛔ Fatal error - stopping attempts")
                return False
            elif code in continue_errors:
                print(f"       🔄 Retryable error - continuing with next format")
                return True
            else:
                print(f"       ❓ Unknown error code - continuing")
                return True
                
        except Exception as e:
            print(f"       💥 Error handling exception: {e}")
            return True

    def _copy_via_image_node_uri(self, image_uri: str, target_album_key: str) -> Tuple[bool, str]:
        """Try using the exact URI from image details"""
        try:
            if not image_uri:
                return False, "No image URI available"
                
            url = f"https://api.smugmug.com/api/v2/album/{target_album_key}!collectimages"
            print(f"   🔍 Trying with exact image URI: {image_uri}")
            
            collect_data = {'CollectUris': [image_uri]}
            success, response_data = self._make_collect_request(url, collect_data)
            
            if success:
                print(f"   ✅ SUCCESS with exact image URI!")
                return True, f"Image copied via exact URI from image details"
            
            return False, "exact image URI failed"
            
        except Exception as e:
            return False, f"Exact URI error: {str(e)}"

    def _copy_via_alternative_endpoints(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Try alternative SmugMug endpoints"""
        try:
            # Alternative approach: Try using different endpoint structures
            alt_endpoints = [
                f"https://api.smugmug.com/api/v2/image/{image_id}!collect",
                f"https://api.smugmug.com/api/v2/album/{target_album_key}!moveimages",
            ]
            
            for endpoint in alt_endpoints:
                print(f"   🔍 Trying alternative endpoint: {endpoint}")
                
                if "!collect" in endpoint:
                    data = {'AlbumUri': f"/api/v2/album/{target_album_key}"}
                elif "!moveimages" in endpoint:
                    data = {'ImageUris': [f"/api/v2/image/{image_id}"]}
                else:
                    continue
                
                success, response_data = self._make_collect_request(endpoint, data)
                
                if success:
                    print(f"   ✅ SUCCESS with alternative endpoint!")
                    return True, f"Image copied via alternative endpoint"
            
            return False, "all alternative endpoints failed"
            
        except Exception as e:
            return False, f"Alternative endpoint error: {str(e)}"

    def _debug_api_response(self, image_id: str, target_album_key: str) -> dict:
        """Debug API responses to understand what's wrong"""
        debug_info = {
            'image_id': image_id,
            'album_key': target_album_key,
            'image_access': None,
            'album_access': None
        }
        
        try:
            # Test basic image access
            image_url = f"https://api.smugmug.com/api/v2/image/{image_id}"
            auth = OAuth1(
                client_key=self.api.api_key,
                client_secret=self.api.api_secret,
                resource_owner_key=self.api.access_token,
                resource_owner_secret=self.api.access_secret,
                signature_method='HMAC-SHA1',
                signature_type='AUTH_HEADER'
            )
            
            print(f"   🔍 DEBUG: Testing image access: {image_url}")
            response = requests.get(image_url, auth=auth, allow_redirects=False, timeout=10)
            debug_info['image_access'] = {
                'status': response.status_code,
                'accessible': response.status_code in [200, 301, 302]
            }
            print(f"   🔍 Image access result: {response.status_code}")
            
            # Test basic album access
            album_url = f"https://api.smugmug.com/api/v2/album/{target_album_key}"
            print(f"   🔍 DEBUG: Testing album access: {album_url}")
            response = requests.get(album_url, auth=auth, allow_redirects=False, timeout=10)
            debug_info['album_access'] = {
                'status': response.status_code,
                'accessible': response.status_code in [200, 301, 302]
            }
            print(f"   🔍 Album access result: {response.status_code}")
            
        except Exception as e:
            debug_info['debug_error'] = str(e)
            print(f"   ❌ Debug failed: {e}")
        
        return debug_info

    def _provide_enhanced_manual_instructions(self, image_id: str, target_album_key: str, debug_info: dict) -> Tuple[bool, str]:
        """Provide enhanced manual instructions with debug information"""
        try:
            image_details = self.api.get_image_details(image_id)
            album_info = self.api.get_album_info(target_album_key)
            
            image_name = image_details.get('FileName', f'Image {image_id}') if image_details else f'Image {image_id}'
            album_name = album_info.get('name', 'Review Album') if album_info else 'Review Album'
            
            manual_msg = f"All API copy methods failed - Manual copy needed: {image_name} → {album_name}"
            
            print(f"   💡 {manual_msg}")
            print(f"      Image ID: {image_id}")
            print(f"      Target Album: {target_album_key}")
            print(f"      Debug info: {debug_info}")
            print(f"      💡 Use SmugMug's 'Collect' feature to manually add this image")
            print(f"      🔍 Consider checking album permissions and image accessibility")
            
            return False, manual_msg
            
        except Exception as e:
            return False, f"Could not generate enhanced manual instructions: {str(e)}"
