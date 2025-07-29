"""
SmugMug API Adapter for MugMatch v2.1 - FIXED VERSION
File: smugmug_api.py
Incorporates the redirect handling fix from SmugMug engineering
This resolves the OAuth nonce_used errors
"""

import requests
from requests_oauthlib import OAuth1
import json
from typing import Dict, List, Optional, Tuple
import time

class SmugMugAPIAdapter:
    """
    Fixed SmugMug API adapter that handles redirects properly
    This resolves the OAuth nonce_used errors
    """
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.base_url = "https://api.smugmug.com/api/v2"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        print(f"SmugMug API initialized with FIXED redirect handling")
    
    def _create_oauth(self) -> OAuth1:
        """Create fresh OAuth instance for each request"""
        return OAuth1(
            client_key=self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
    
    def _make_request(self, url: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """
        Make API request with FIXED redirect handling
        KEY FIX: Disables automatic redirects and handles them manually with fresh OAuth
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        try:
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'MugMatch/2.0-Fixed'
            }
            
            if data and method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                headers['Content-Type'] = 'application/json'
            
            # Create fresh OAuth for each request
            auth = self._create_oauth()
            
            # CRITICAL FIX: Disable automatic redirects
            if method == 'GET':
                response = requests.get(url, auth=auth, headers=headers, params=params, 
                                      allow_redirects=False, timeout=30)
            elif method == 'POST':
                response = requests.post(url, auth=auth, headers=headers, params=params, json=data,
                                       allow_redirects=False, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, auth=auth, headers=headers, params=params,
                                         allow_redirects=False, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, auth=auth, headers=headers, params=params, json=data,
                                      allow_redirects=False, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, auth=auth, headers=headers, params=params, json=data,
                                        allow_redirects=False, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            # Handle the response (including redirects)
            return self._handle_response_with_redirects(response, method, params, data)
                
        except Exception as e:
            print(f"API request error: {e}")
            return None
    
    def _handle_response_with_redirects(self, response: requests.Response, 
                                       original_method: str = 'GET', 
                                       original_params: Dict = None, 
                                       original_data: Dict = None) -> Optional[Dict]:
        """Handle response that might be a redirect - KEY FIX from SmugMug engineering"""
        
        if not response:
            return None
        
        # Handle redirect responses (3xx) - SmugMug engineering's fix
        if 300 <= response.status_code < 400:
            redirect_location = response.headers.get('Location', '')
            
            if redirect_location:
                # Handle both absolute and relative URLs
                if redirect_location.startswith('http'):
                    redirect_url = redirect_location
                else:
                    # Convert relative URL to absolute
                    if redirect_location.startswith('/'):
                        redirect_url = f"https://api.smugmug.com{redirect_location}"
                    else:
                        redirect_url = f"https://api.smugmug.com/api/v2/{redirect_location}"
                
                print(f"🔄 Following redirect: {redirect_url}")
                
                # Make new request to redirect URL with FRESH OAuth
                return self._make_request(redirect_url, original_method, original_params, original_data)
            else:
                print(f"❌ Redirect response without Location header")
                return None
        
        # Handle success responses
        elif response.status_code in [200, 201, 204]:
            try:
                return response.json() if response.text else {'status': 'success'}
            except:
                return {'status': 'success', 'text': response.text}
        
        # Handle rate limiting
        elif response.status_code == 429:
            print("Rate limited, waiting 5 seconds...")
            time.sleep(5)
            return self._make_request(response.url, original_method, original_params, original_data)
        
        # Handle error responses
        else:
            print(f"API request failed: {response.status_code} - {response.text[:200]}")
            return None
    
    def get_user_albums(self, user_name: str) -> List[Dict]:
        """Fetch all albums for a user using SmugMug API v2"""
        albums = []
        start = 1
        count = 100
        
        print(f"Fetching albums for user: {user_name}")
        
        while True:
            url = f"{self.base_url}/user/{user_name}!albums"
            params = {
                'start': start,
                'count': count,
                '_expand': 'ImageCount',
                '_filter': 'Title,Name,AlbumKey,ImageCount,NodeID,WebUri,Privacy'
            }
            
            response = self._make_request(url, 'GET', params)
            
            if not response or 'Response' not in response:
                break
            
            album_data = response['Response'].get('Album', [])
            if not album_data:
                break
            
            for album in album_data:
                albums.append({
                    'id': album.get('AlbumKey', ''),
                    'name': album.get('Name', album.get('Title', 'Untitled Album')),
                    'image_count': album.get('ImageCount', 0),
                    'url': album.get('WebUri', ''),
                    'node_id': album.get('NodeID', ''),
                    'privacy': album.get('Privacy', 'Public')
                })
            
            if len(album_data) < count:
                break
            
            start += count
        
        print(f"Total albums found: {len(albums)}")
        return albums
    
    def get_album_images(self, album_key: str) -> List[Dict]:
        """Fetch all images from an album with their MD5 hashes and thumbnail URLs"""
        images = []
        start = 1
        count = 100
        
        print(f"Fetching images for album: {album_key}")
        
        # Get album info for metadata
        album_info = self.get_album_info(album_key)
        album_name = album_info.get('name', 'Unknown Album') if album_info else 'Unknown Album'
        
        while True:
            url = f"{self.base_url}/album/{album_key}!images"
            params = {
                'start': start,
                'count': count,
                '_filter': 'ImageKey,FileName,ArchivedMD5,ArchivedSize,Date,WebUri,ThumbnailUrl'
            }
            
            response = self._make_request(url, 'GET', params)
            
            if not response or 'Response' not in response:
                break
            
            image_data = response['Response'].get('AlbumImage', [])
            if not image_data:
                break
            
            for image in image_data:
                image_key = image.get('ImageKey', '')
                if not image_key:
                    continue
                
                try:
                    md5_hash = image.get('ArchivedMD5', '')
                    if not md5_hash:
                        continue
                    
                    images.append({
                        'image_id': image_key,
                        'filename': image.get('FileName', f"image_{image_key}"),
                        'album_name': album_name,
                        'album_id': album_key,
                        'md5_hash': md5_hash,
                        'url': image.get('WebUri', ''),
                        'size': image.get('ArchivedSize', 0),
                        'date_uploaded': image.get('Date', ''),
                        'thumbnail_url': image.get('ThumbnailUrl', '')
                    })
                    
                except Exception as e:
                    print(f"Error processing image {image_key}: {e}")
                    continue
            
            if len(image_data) < count:
                break
            
            start += count
        
        print(f"Total images found in album {album_key}: {len(images)}")
        return images
    
    def get_album_info(self, album_key: str) -> Optional[Dict]:
        """Get basic album information using SmugMug API v2"""
        url = f"{self.base_url}/album/{album_key}"
        params = {
            '_filter': 'AlbumKey,Name,Title,ImageCount,WebUri,NodeID'
        }
        
        response = self._make_request(url, 'GET', params)
        
        if response and 'Response' in response:
            album = response['Response']['Album']
            return {
                'id': album.get('AlbumKey', ''),
                'name': album.get('Name', album.get('Title', 'Untitled Album')),
                'image_count': album.get('ImageCount', 0),
                'url': album.get('WebUri', '')
            }
        
        return None
    
    def get_image_details(self, image_key: str) -> Optional[Dict]:
        """Get detailed information about a specific image"""
        url = f"{self.base_url}/image/{image_key}"
        response = self._make_request(url, 'GET')
        
        if response and 'Response' in response:
            return response['Response']['Image']
        
        return None
    
    def delete_image_with_details(self, image_key: str) -> Tuple[bool, str]:
        """Delete an image from SmugMug - NOW WORKING with redirect fix!"""
        try:
            print(f"🗑️ Deleting image: {image_key}")
            
            url = f"{self.base_url}/image/{image_key}"
            response = self._make_request(url, 'DELETE')
            
            if response:
                # Check for success indicators - SmugMug returns "Ok" for successful deletes
                success_indicators = [
                    response.get('status') == 'success',
                    'status' in response,
                    response.get('text') == 'Ok',
                    response.get('Message') == 'Ok',
                    # Handle the case where the entire response is just {'text': 'Ok'}
                    str(response).strip() == "{'text': 'Ok'}",
                    # Handle direct "Ok" response
                    response == 'Ok' or str(response) == 'Ok'
                ]
                
                if any(success_indicators):
                    print(f"✅ Successfully deleted image {image_key}")
                    return True, "Image deleted successfully"
                else:
                    # Log the actual response for debugging
                    print(f"🔍 Unexpected response format: {response}")
                    error_msg = response.get('Message', f'Unexpected response: {response}')
                    print(f"❌ Delete failed: {error_msg}")
                    return False, error_msg
            else:
                print(f"❌ No response from delete request")
                return False, "No response from server"
                
        except Exception as e:
            print(f"❌ Exception during delete: {e}")
            return False, f"Delete error: {str(e)}"
    
    def delete_image(self, image_key: str) -> bool:
        """Simple delete method for backward compatibility"""
        success, _ = self.delete_image_with_details(image_key)
        return success
    
    def get_user_info(self, user_name: str) -> Optional[Dict]:
        """Get authenticated user information using SmugMug API v2"""
        url = f"{self.base_url}!authuser"
        response = self._make_request(url, 'GET')
        
        if response and 'Response' in response:
            user_data = response['Response'].get('User', {})
            return {
                'Name': user_data.get('Name', user_name),
                'NickName': user_data.get('NickName', user_name),  
                'RefTag': user_data.get('RefTag', user_name)
            }
        
        return None


# Integration functions
def create_smugmug_api(credentials_file: str = "credentials.py") -> SmugMugAPIAdapter:
    """Create a SmugMug API instance using your existing credentials file"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("credentials", credentials_file)
        credentials = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(credentials)
        
        return SmugMugAPIAdapter(
            api_key=credentials.API_KEY,
            api_secret=credentials.API_SECRET,
            access_token=credentials.ACCESS_TOKEN,
            access_secret=credentials.ACCESS_SECRET
        )
    
    except Exception as e:
        print(f"Failed to load credentials from {credentials_file}: {e}")
        return None


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
