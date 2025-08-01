#!/usr/bin/env python3
"""
SmugMug Album Operations - Album creation and management functionality v5.0
File: smugmug_album_operations.py
Contains the album creation and management methods separated from image copying
"""

import requests
from requests_oauthlib import OAuth1
import json
from typing import Dict, List, Optional
from datetime import datetime

class SmugMugAlbumOperations:
    """SmugMug album creation and management operations"""
    
    def __init__(self, api_adapter):
        self.api = api_adapter
        self.review_album_cache = {}
        
    def find_or_create_review_album(self, username: str) -> Optional[Dict]:
        """Find existing review album or create a new one"""
        try:
            print(f"🔍 Finding or creating SmugDups review album for {username}")
            
            # Step 1: Check for existing SmugDups review albums
            existing_album = self._find_existing_smugdups_album(username)
            if existing_album:
                return existing_album
            
            # Step 2: Create new album using working method
            return self._create_new_review_album_working(username)
            
        except Exception as e:
            print(f"❌ Error in find_or_create_review_album: {e}")
            return None
    
    def _find_existing_smugdups_album(self, username: str) -> Optional[Dict]:
        """Look for existing SmugDups review albums"""
        try:
            print("   Checking for existing SmugDups albums...")
            albums = self.api.get_user_albums(username)
            
            smugdups_albums = []
            for album in albums:
                album_name = album.get('name', '').lower()
                if ('smugdups' in album_name and 'review' in album_name) or \
                   ('duplicate' in album_name and 'review' in album_name):
                    smugdups_albums.append(album)
            
            if smugdups_albums:
                # Use the most recent one (or first one found)
                album = smugdups_albums[0]
                album_info = {
                    'album_key': album['id'],
                    'album_name': album['name'],
                    'web_url': album['url'],
                    'image_count': album['image_count'],
                    'method': 'found_existing'
                }
                print(f"   ✅ Found existing SmugDups album: {album['name']}")
                return album_info
            
            print("   No existing SmugDups albums found")
            return None
            
        except Exception as e:
            print(f"   Error checking existing albums: {e}")
            return None
    
    def _create_new_review_album_working(self, username: str) -> Optional[Dict]:
        """Create new review album using the working method"""
        try:
            # Use date only for consistent naming
            date_stamp = datetime.now().strftime("%Y%m%d")
            album_name = f"SmugDups Review {date_stamp}"
            # CRITICAL: UrlName must start with uppercase letter!
            url_name = f"SmugDups-review-{date_stamp}"
            
            print(f"   Creating new album: {album_name}")
            print(f"   Using UrlName: {url_name}")
            
            # Use the working endpoint and parameters
            album_info = self._create_album_working_method(album_name, url_name, username)
            if album_info:
                return album_info
            
            # Fallback to manual creation with proper instructions
            return self._provide_manual_creation_instructions(album_name, url_name)
            
        except Exception as e:
            print(f"   Error creating new album: {e}")
            return None
    
    def _create_album_working_method(self, album_name: str, url_name: str, username: str) -> Optional[Dict]:
        """Create album using the working method from our testing"""
        try:
            print(f"   Trying WORKING album creation method...")
            
            # Working endpoint discovered through testing
            album_url = f"https://api.smugmug.com/api/v2/folder/user/{username}!albums"
            
            # Working album data with all required parameters
            album_data = {
                'Name': album_name,                    # Display name
                'UrlName': url_name,                   # REQUIRED: URL-friendly name (must start uppercase!)
                'Privacy': 'Unlisted',                 # Safe privacy setting
                'Description': f'SmugDups duplicate review album created {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'Keywords': 'SmugDups,Duplicates,Review',
                'SortMethod': 'Date Uploaded',
                'SortDirection': 'Descending'
            }
            
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
                'User-Agent': 'SmugDups/5.0-AlbumCreation'
            }
            
            response = requests.post(
                album_url,
                auth=auth,
                headers=headers,
                json=album_data,
                timeout=30
            )
            
            print(f"   Response: {response.status_code} - {response.reason}")
            
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    if 'Response' in data and 'Album' in data['Response']:
                        album = data['Response']['Album']
                        album_key = album.get('AlbumKey', '')
                        web_uri = album.get('WebUri', '')
                        
                        if album_key:
                            album_info = {
                                'album_key': album_key,
                                'album_name': album.get('Name', album_name),
                                'web_url': web_uri or f'https://smugmug.com/album/{album_key}',
                                'image_count': 0,
                                'method': 'api_creation_working',
                                'url_name': album.get('UrlName', url_name),
                                'created_at': datetime.now().isoformat()
                            }
                            
                            print(f"   ✅ Album created successfully!")
                            print(f"      Key: {album_key}")
                            print(f"      URL: {album_info['web_url']}")
                            
                            return album_info
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
            
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Album creation failed: {error_data.get('Message', 'Unknown error')}")
                except:
                    print(f"   ❌ Album creation failed: HTTP {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f"   Error with working album creation method: {e}")
            return None
    
    def _provide_manual_creation_instructions(self, album_name: str, url_name: str) -> Dict:
        """Provide manual creation instructions as fallback"""
        print(f"   ⚠️  Automatic creation failed, providing manual instructions")
        
        return {
            'album_key': None,
            'album_name': album_name,
            'web_url': None,
            'image_count': 0,
            'method': 'manual_required',
            'manual_creation_needed': True,
            'instructions': f"""
MANUAL ALBUM CREATION REQUIRED:

1. Go to SmugMug.com and log in
2. Create a new album named: {album_name}
3. Important: Set the URL name to: {url_name}
4. Set privacy to 'Unlisted' (recommended)
5. Add description: 'SmugDups duplicate review album'
6. Save the album
7. Re-run SmugDups to detect the new album

The album will be automatically detected on the next scan.

💡 TIP: The URL name format ({url_name}) ensures proper detection.
""".strip(),
            'suggested_album_name': album_name,
            'suggested_url_name': url_name
        }
