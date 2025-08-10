"""
Core data models for SmugDups v5.1 - Geographic Data Addition
File: core/models.py
ENHANCEMENT: Added GPS coordinates support (latitude, longitude, altitude)
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import math

@dataclass
class DuplicatePhoto:
    """Duplicate photo with GPS coordinate support"""
    image_id: str
    filename: str
    album_name: str
    album_id: str
    md5_hash: str
    url: str
    size: int
    date_uploaded: str
    thumbnail_url: str = ""
    keep: bool = False
    
    # Enhanced metadata fields (existing)
    title: str = ""
    caption: str = ""
    keywords: str = ""
    date_taken: str = ""  # Date photo was actually taken
    
    # NEW: Geographic data
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"DuplicatePhoto({self.filename} from {self.album_name})"
    
    def size_mb(self) -> float:
        """Return file size in megabytes"""
        return self.size / (1024 * 1024) if self.size > 0 else 0.0
    
    def short_filename(self, max_length: int = 25) -> str:
        """Return shortened filename for display"""
        if len(self.filename) <= max_length:
            return self.filename
        return self.filename[:max_length-3] + "..."
    
    def short_album_name(self, max_length: int = 22) -> str:
        """Return shortened album name for display"""
        if len(self.album_name) <= max_length:
            return self.album_name
        return self.album_name[:max_length-3] + "..."
    
    # NEW: Geographic methods
    def has_location(self) -> bool:
        """Check if photo has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None
    
    def get_location_string(self) -> str:
        """Get formatted location string"""
        if not self.has_location():
            return ""
        
        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"
        
        lat_str = f"{abs(self.latitude):.6f}°{lat_dir}"
        lon_str = f"{abs(self.longitude):.6f}°{lon_dir}"
        
        result = f"{lat_str}, {lon_str}"
        
        if self.altitude is not None:
            if self.altitude >= 0:
                result += f" @{self.altitude:.0f}m"
            else:
                result += f" @{abs(self.altitude):.0f}m below sea level"
        
        return result
    
    def get_location_short(self) -> str:
        """Get short location string for display"""
        if not self.has_location():
            return ""
        return f"{self.latitude:.4f}, {self.longitude:.4f}"
    
    def calculate_distance_to(self, other: 'DuplicatePhoto') -> Optional[float]:
        """Calculate distance in kilometers to another photo with GPS coords"""
        if not self.has_location() or not other.has_location():
            return None
        
        # Haversine formula for distance between two points on Earth
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        return 6371 * c
    
    # Title methods
    def has_title(self) -> bool:
        """Check if photo has a title"""
        return bool(self.title and self.title.strip())
    
    def display_title(self, max_length: int = 30) -> str:
        """Return title for display, truncated if needed"""
        if not self.has_title():
            return ""
        
        title = self.title.strip()
        if len(title) <= max_length:
            return title
        return title[:max_length-3] + "..."
    
    # Caption methods
    def has_caption(self) -> bool:
        """Check if photo has a caption"""
        return bool(self.caption and self.caption.strip())
    
    def display_caption(self, max_length: int = 150) -> str:
        """Return caption for display, truncated if needed"""
        if not self.has_caption():
            return ""
        
        caption = self.caption.strip()
        if len(caption) <= max_length:
            return caption
        return caption[:max_length-3] + "..."
    
    # Keywords methods
    def has_keywords(self) -> bool:
        """Check if photo has keywords"""
        return bool(self.keywords and self.keywords.strip())
    
    def get_keywords_list(self) -> List[str]:
        """Return keywords as a list"""
        if not self.has_keywords():
            return []
        return [k.strip() for k in self.keywords.split(',') if k.strip()]
    
    def display_keywords(self, max_keywords: int = 8) -> str:
        """Return keywords for display, limited count"""
        keywords_list = self.get_keywords_list()
        if not keywords_list:
            return ""
        
        if len(keywords_list) <= max_keywords:
            return ", ".join(keywords_list)
        else:
            displayed = keywords_list[:max_keywords]
            remaining = len(keywords_list) - max_keywords
            return ", ".join(displayed) + f" (+{remaining} more)"
    
    # Date comparison methods
    def has_date_taken(self) -> bool:
        """Check if photo has date taken information"""
        return bool(self.date_taken and self.date_taken.strip())
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse SmugMug date string to datetime object"""
        if not date_string:
            return None
        
        try:
            # Handle different SmugMug date formats
            if 'T' in date_string:
                # ISO format: 2024-03-15T18:30:42Z
                clean_date = date_string.replace('Z', '+00:00')
                return datetime.fromisoformat(clean_date)
            else:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(date_string, fmt)
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Date parsing error for '{date_string}': {e}")
        
        return None
    
    def get_date_taken_datetime(self) -> Optional[datetime]:
        """Get date taken as datetime object"""
        return self.parse_date(self.date_taken)
    
    def get_date_uploaded_datetime(self) -> Optional[datetime]:
        """Get date uploaded as datetime object"""
        return self.parse_date(self.date_uploaded)
    
    def get_date_comparison(self) -> dict:
        """Compare date taken vs date uploaded"""
        date_taken_dt = self.get_date_taken_datetime()
        date_uploaded_dt = self.get_date_uploaded_datetime()
        
        result = {
            'has_both_dates': bool(date_taken_dt and date_uploaded_dt),
            'date_taken_formatted': '',
            'date_uploaded_formatted': '',
            'time_difference': '',
            'difference_days': 0,
            'status': 'unknown'
        }
        
        # Format dates for display
        if date_taken_dt:
            result['date_taken_formatted'] = date_taken_dt.strftime('%Y-%m-%d %H:%M')
        
        if date_uploaded_dt:
            result['date_uploaded_formatted'] = date_uploaded_dt.strftime('%Y-%m-%d %H:%M')
        
        # Calculate difference if both dates available
        if result['has_both_dates']:
            diff = date_uploaded_dt - date_taken_dt
            days = diff.days
            hours = diff.seconds // 3600
            
            result['difference_days'] = days
            
            # Format time difference
            if days == 0:
                if hours == 0:
                    result['time_difference'] = 'Same day'
                    result['status'] = 'immediate'
                else:
                    result['time_difference'] = f'{hours} hours later'
                    result['status'] = 'same_day'
            elif days == 1:
                result['time_difference'] = '1 day later'
                result['status'] = 'recent'
            elif days < 7:
                result['time_difference'] = f'{days} days later'
                result['status'] = 'recent'
            elif days < 30:
                weeks = days // 7
                result['time_difference'] = f'{weeks} week{"s" if weeks > 1 else ""} later'
                result['status'] = 'delayed'
            elif days < 365:
                months = days // 30
                result['time_difference'] = f'{months} month{"s" if months > 1 else ""} later'
                result['status'] = 'very_delayed'
            else:
                years = days // 365
                result['time_difference'] = f'{years} year{"s" if years > 1 else ""} later'
                result['status'] = 'archived'
        
        return result
    
    def has_enhanced_metadata(self) -> bool:
        """Check if photo has rich metadata worth displaying in expandable section"""
        return any([
            self.has_caption(), 
            self.has_keywords(),
            self.has_date_taken(),
            self.has_location()  # NEW: Include location in enhanced metadata
        ])
    
    def get_quality_score(self) -> int:
        """Calculate a quality score to help determine which duplicate to keep"""
        score = 0
        
        # File size bonus (larger files often better quality)
        if self.size > 5 * 1024 * 1024:  # > 5MB
            score += 3
        elif self.size > 1 * 1024 * 1024:  # > 1MB
            score += 2
        elif self.size > 500 * 1024:  # > 500KB
            score += 1
        
        # Metadata richness bonus
        if self.has_title():
            score += 2
        if self.has_caption():
            score += 2
        if self.has_keywords():
            score += 1
        if self.has_date_taken():
            score += 1
        if self.has_location():  # NEW: GPS coordinates add to quality score
            score += 1
        
        # Date comparison bonus (photos uploaded soon after being taken are often originals)
        date_comp = self.get_date_comparison()
        if date_comp['has_both_dates']:
            if date_comp['status'] in ['immediate', 'same_day']:
                score += 3  # Likely original upload
            elif date_comp['status'] == 'recent':
                score += 1
        
        return score
