"""
SmugMug Album/Folder Operations for SmugDups - FINAL FIXED VERSION
Uses correct SmugMug API endpoints for album creation
"""

import requests
from requests_oauthlib import OAuth1
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class SmugMugFolderOperations:
    """Handle album creation and image moving operations - Final fixed version"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.base_url = "https://api.smugmug.com/api/v2"
        
        # Cache for created albums to avoid duplicates
        self.created_albums = {}
        
    def _create_oauth(self) -> OAuth1:
        """Create fresh OAuth instance"""
        return OAuth1(
            client_key=self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
    
    def _make_request(self, url: str, method: str = 'GET', data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            auth = self._create_oauth()
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'SmugDups/2.0-FolderOps-Final'
            }
            
            if data and method in ['POST', 'PUT', 'PATCH']:
                headers['Content-Type'] = 'application/json'
            
            if method == 'GET':
                response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, auth=auth, headers=headers, json=data, params=params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, auth=auth, headers=headers, json=data, params=params, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, auth=auth, headers=headers, json=data, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, auth=auth, headers=headers, params=params, timeout=30)
            
            print(f"{method} {url} -> {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text[:300]}")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_user_info_with_node(self, username: str) -> Optional[Dict]:
        """Get user info and try to extract node information"""
        
        # Try different approaches to get user data with node info
        approaches = [
            # Method 1: authuser with expansions
            {
                'url': f"{self.base_url}!authuser",
                'params': {'_expand': 'Node,Folder'},
                'description': 'authuser with Node expansion'
            },
            # Method 2: user endpoint with expansions  
            {
                'url': f"{self.base_url}/user/{username}",
                'params': {'_expand': 'Node,Folder,Albums'},
                'description': 'user endpoint with expansions'
            },
            # Method 3: user endpoint with different filters
            {
                'url': f"{self.base_url}/user/{username}",
                'params': {'_filter': 'NodeID,Name,NickName,Folder'},
                'description': 'user endpoint with NodeID filter'
            },
            # Method 4: just basic user info
            {
                'url': f"{self.base_url}/user/{username}",
                'params': {},
                'description': 'basic user endpoint'
            }
        ]
        
        for approach in approaches:
            try:
                print(f"Trying: {approach['description']}...")
                response = self._make_request(approach['url'], params=approach['params'])
                
                if response and 'Response' in response:
                    user_data = response['Response']['User']
                    
                    # Check for NodeID in various places
                    node_id = user_data.get('NodeID', '')
                    if node_id:
                        print(f"✅ Found NodeID: {node_id}")
                        return {'node_id': node_id, 'user_data': user_data}
                    
                    # Check for nested Node object
                    node_obj = user_data.get('Node', {})
                    if isinstance(node_obj, dict):
                        node_id = node_obj.get('NodeID', '')
                        if node_id:
                            print(f"✅ Found NodeID in nested Node: {node_id}")
                            return {'node_id': node_id, 'user_data': user_data}
                    
                    # Check for Folder with NodeID
                    folder_obj = user_data.get('Folder', {})
                    if isinstance(folder_obj, dict):
                        node_id = folder_obj.get('NodeID', '')
                        if node_id:
                            print(f"✅ Found NodeID in Folder: {node_id}")
                            return {'node_id': node_id, 'user_data': user_data}
                    
                    print(f"   No NodeID found, available keys: {list(user_data.keys())}")
                
            except Exception as e:
                print(f"   Method failed: {e}")
                continue
        
        print("⚠️  Could not find NodeID through any method")
        return None
    
    def create_album_using_albums_endpoint(self, album_name: str, username: str) -> Optional[Dict]:
        """Create album using the correct SmugMug albums endpoint"""
        try:
            print(f"Creating album using albums endpoint: {album_name}")
            
            # Use the correct endpoint for creating albums
            url = f"{self.base_url}!albums"
            
            album_data = {
                'Name': album_name,
                'Privacy': 'Unlisted',
                'Description': f'SmugDups duplicate review album created {datetime.now().isoformat()}',
                'SortMethod': 'DateTimeOriginal',
                'SortDirection': 'Ascending',
                'Keywords': ['SmugDups', 'Duplicates', 'Review'],
                'SmugSearchable': False,
                'WorldSearchable': False
            }
            
            response = self._make_request(url, 'POST', album_data)
            
            if response and 'Response' in response:
                album_resp = response['Response']['Album']
                album_key = album_resp['AlbumKey']
                web_uri = album_resp.get('WebUri', f'https://smugmug.com/album/{album_key}')
                
                print(f"✅ Created album: {album_name} (Key: {album_key})")
                
                return {
                    'album_key': album_key,
                    'album_name': album_name,
                    'web_url': web_uri,
                    'created_at': datetime.now().isoformat()
                }
            else:
                print("❌ Failed to create album via albums endpoint")
                return None
                
        except Exception as e:
            print(f"Error creating album via albums endpoint: {e}")
            return None
    
    def find_or_create_mugmatch_folder(self, username: str) -> Optional[str]:
        """Find existing SmugDups folder or create a new one"""
        try:
            print("Looking for existing SmugDups folders...")
            
            # Get user's albums to see if we have any SmugDups folders
            albums_url = f"{self.base_url}/user/{username}!albums"
            params = {'_filter': 'Name,AlbumKey,Description'}
            
            response = self._make_request(albums_url, params=params)
            
            if response and 'Response' in response:
                albums = response['Response'].get('Album', [])
                
                # Look for existing SmugDups albums
                for album in albums:
                    album_name = album.get('Name', '')
                    if 'SmugDups' in album_name and 'Review' in album_name:
                        album_key = album.get('AlbumKey', '')
                        if album_key:
                            print(f"✅ Found existing SmugDups review album: {album_name}")
                            return album_key
            
            # If no existing album found, create a new one
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            album_name = f"MugMatch_Review_{timestamp}"
            
            album_info = self.create_album_using_albums_endpoint(album_name, username)
            
            if album_info:
                return album_info['album_key']
            else:
                return None
                
        except Exception as e:
            print(f"Error finding/creating SmugDups folder: {e}")
            return None
    
    def setup_review_system(self, username: str) -> Optional[Dict[str, str]]:
        """Set up review system using the most reliable method"""
        try:
            print(f"🔧 Setting up review system for {username}...")
            
            # Try to find or create a SmugDups review album
            album_key = self.find_or_create_mugmatch_folder(username)
            
            if album_key:
                # Get album details
                album_url = f"{self.base_url}/album/{album_key}"
                album_response = self._make_request(album_url)
                
                if album_response and 'Response' in album_response:
                    album_data = album_response['Response']['Album']
                    album_name = album_data.get('Name', 'SmugDups Review')
                    web_uri = album_data.get('WebUri', f'https://smugmug.com/album/{album_key}')
                    
                    review_info = {
                        'folder_name': 'User Albums (no folder structure)',
                        'folder_node': 'N/A',
                        'album_name': album_name,
                        'album_key': album_key,
                        'created_at': datetime.now().isoformat(),
                        'web_url': web_uri,
                        'setup_method': 'albums_endpoint'
                    }
                    
                    print(f"\n✅ Review system set up successfully!")
                    print(f"   📸 Album: {album_name}")
                    print(f"   🔑 Album Key: {album_key}")
                    print(f"   🌐 Web URL: {web_uri}")
                    
                    return review_info
            
            print("❌ Could not set up review system")
            return None
                
        except Exception as e:
            print(f"Error setting up review system: {e}")
            return None
    
    def copy_image_to_album(self, image_id: str, target_album_key: str) -> Tuple[bool, str]:
        """Copy an image to target album"""
        try:
            print(f"Copying image {image_id} to album {target_album_key}")
            
            # Use the correct endpoint for adding images to albums
            url = f"{self.base_url}/album/{target_album_key}!albumimages"
            
            data = {
                'AlbumImages': [{'ImageKey': image_id}]
            }
            
            response = self._make_request(url, 'POST', data)
            
            if response:
                print("✅ Image copied to review album")
                return True, "Image successfully copied to review album"
            else:
                return False, "Failed to copy image to review album"
                
        except Exception as e:
            return False, f"Copy operation failed: {str(e)}"
    
    def process_duplicate_group_to_review(self, duplicate_group: List[Dict], review_album_key: str) -> Dict[str, bool]:
        """Process a group of duplicates by copying them to review album"""
        results = {}
        
        print(f"\n📋 Processing duplicate group ({len(duplicate_group)} images)")
        
        for i, photo in enumerate(duplicate_group):
            image_id = photo['image_id']
            filename = photo['filename']
            album_name = photo['album_name']
            
            print(f"  {i+1}/{len(duplicate_group)}: {filename} from {album_name}")
            
            # Copy to review album
            success, message = self.copy_image_to_album(image_id, review_album_key)
            results[image_id] = success
            
            if success:
                print(f"    ✅ {message}")
            else:
                print(f"    ❌ {message}")
            
            # Small delay to avoid rate limiting
            time.sleep(1.0)  # Increased delay for safety
        
        successful = sum(1 for success in results.values() if success)
        print(f"  📊 Results: {successful}/{len(duplicate_group)} images copied to review")
        
        return results
    
    def test_image_operations(self, album_key: str, test_image_id: str = "CFGhfc5") -> bool:
        """Test copying an image to the review album"""
        print(f"\n🧪 Testing image copy with image {test_image_id}...")
        
        success, message = self.copy_image_to_album(test_image_id, album_key)
        
        if success:
            print(f"✅ Image copy test successful: {message}")
            return True
        else:
            print(f"❌ Image copy test failed: {message}")
            return False


def test_complete_system():
    """Test the complete review system"""
    try:
        import credentials
        
        print("🧪 COMPLETE SMUGMUG REVIEW SYSTEM TEST")
        print("="*60)
        
        folder_ops = SmugMugFolderOperations(
            api_key=credentials.API_KEY,
            api_secret=credentials.API_SECRET,
            access_token=credentials.ACCESS_TOKEN,
            access_secret=credentials.ACCESS_SECRET
        )
        
        # Test 1: Set up review system
        print("\n📋 Step 1: Setting up review system...")
        review_info = folder_ops.setup_review_system(credentials.USER_NAME)
        
        if not review_info:
            print("❌ Could not set up review system")
            return False
        
        print(f"✅ Review system created successfully!")
        
        # Test 2: Test image copying
        print(f"\n📋 Step 2: Testing image copy...")
        album_key = review_info['album_key']
        test_success = folder_ops.test_image_operations(album_key)
        
        # Test 3: Test duplicate group processing
        if test_success:
            print(f"\n📋 Step 3: Testing duplicate group processing...")
            
            # Create mock duplicate group
            mock_duplicates = [
                {
                    'image_id': 'CFGhfc5',
                    'filename': '2021-10-16 11.34.59.jpg',
                    'album_name': 'AAA',
                    'album_id': 'test_album',
                    'md5_hash': 'abc123',
                    'url': 'https://smugmug.com/test',
                    'size': 2500000,
                    'date_uploaded': '2021-10-16T11:34:59Z'
                }
            ]
            
            group_results = folder_ops.process_duplicate_group_to_review(mock_duplicates, album_key)
            group_success = any(group_results.values())
            
            if group_success:
                print("✅ Duplicate group processing successful!")
            else:
                print("❌ Duplicate group processing failed")
        
        # Final summary
        print(f"\n" + "="*60)
        print("FINAL TEST RESULTS")
        print("="*60)
        print(f"✅ Review system setup: SUCCESS")
        print(f"{'✅' if test_success else '❌'} Image copying: {'SUCCESS' if test_success else 'FAILED'}")
        print(f"{'✅' if 'group_success' in locals() and group_success else '❌'} Group processing: {'SUCCESS' if 'group_success' in locals() and group_success else 'FAILED'}")
        
        print(f"\n📊 Review System Details:")
        print(f"   📸 Album: {review_info['album_name']}")
        print(f"   🔑 Key: {review_info['album_key']}")
        print(f"   🌐 URL: {review_info['web_url']}")
        print(f"   📅 Created: {review_info['created_at']}")
        
        if test_success:
            print(f"\n🎉 SUCCESS! The review system is working!")
            print(f"   You can now integrate this into SmugDups")
            print(f"   Visit {review_info['web_url']} to see the test image")
        else:
            print(f"\n⚠️  Review system created but image copying needs work")
        
        return test_success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_complete_system()
