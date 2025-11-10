"""
LastFM API client for making requests to the LastFM web API.
Handles authentication, error handling, and response parsing.
"""

import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

class LastFMAPIError(Exception):
    """Custom exception for LastFM API errors."""
    pass

class LastFMAPIClient:
    """
    Client for interacting with the Last.fm API.
    Handles all API requests and data parsing.
    """
    
    def __init__(self):
        self.api_key = os.getenv("lastfm_key")
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        
        if not self.api_key:
            raise ValueError("LastFM API key not found in environment variables")
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make a request to the LastFM API.
        
        Args:
            params: Request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            LastFMAPIError: If request fails
        """
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for LastFM API errors
            if 'error' in data:
                raise LastFMAPIError(f"LastFM API Error {data['error']}: {data.get('message', 'Unknown error')}")
            
            return data
            
        except requests.RequestException as e:
            raise LastFMAPIError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise LastFMAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        Get user information from LastFM.
        
        Args:
            username: LastFM username
            
        Returns:
            User info dictionary
            
        Raises:
            LastFMAPIError: If API request fails
        """
        params = {
            'method': 'user.getInfo',
            'user': username,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        data = self._make_request(params)
        return data['user']
    
    def get_recent_tracks(self, username: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get recent tracks for a user.
        
        Args:
            username: LastFM username
            limit: Number of tracks to retrieve
            
        Returns:
            Recent tracks data
            
        Raises:
            LastFMAPIError: If API request fails
        """
        params = {
            'method': 'user.getRecentTracks',
            'user': username,
            'api_key': self.api_key,
            'format': 'json',
            'limit': str(limit)
        }
        
        data = self._make_request(params)
        return data.get('recenttracks', {})
    
    def get_track_info(self, artist: str, track: str, username: str = None) -> Dict[str, Any]:
        """
        Get information about a specific track.
        
        Args:
            artist: Artist name
            track: Track name
            username: Optional username for user-specific data
            
        Returns:
            Track info dictionary
            
        Raises:
            LastFMAPIError: If API request fails
        """
        params = {
            'method': 'track.getInfo',
            'artist': artist,
            'track': track,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        if username:
            params['username'] = username
        
        return self._make_request(params)
    
    def get_artist_info(self, artist: str, username: str = None) -> Dict[str, Any]:
        """
        Get information about an artist.
        
        Args:
            artist: Artist name
            username: Optional username for user-specific data
            
        Returns:
            Artist info dictionary
            
        Raises:
            LastFMAPIError: If API request fails
        """
        params = {
            'method': 'artist.getInfo',
            'artist': artist,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        if username:
            params['username'] = username
        
        return self._make_request(params)
    
    def get_album_info(self, artist: str, album: str, username: str = None) -> Dict[str, Any]:
        """
        Get information about an album.
        
        Args:
            artist: Artist name
            album: Album name
            username: Optional username for user-specific data
            
        Returns:
            Album info dictionary
            
        Raises:
            LastFMAPIError: If API request fails
        """
        params = {
            'method': 'album.getInfo',
            'artist': artist,
            'album': album,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        if username:
            params['username'] = username
        
        return self._make_request(params)
    
    def get_track_info(self, artist: str, track: str, username: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed track information.
        
        Args:
            artist: Artist name
            track: Track name
            username: LastFM username
            
        Returns:
            Track info dictionary or None if error
        """
        params = {
            'method': 'track.getInfo',
            'artist': artist,
            'track': track,
            'username': username
        }
        
        response = self._make_request(params)
        return response.get('track') if response else None
    
    def get_artist_info(self, artist: str, username: str) -> Optional[Dict[str, Any]]:
        """
        Get artist information including user stats.
        
        Args:
            artist: Artist name
            username: LastFM username
            
        Returns:
            Artist info dictionary or None if error
        """
        params = {
            'method': 'artist.getInfo',
            'artist': artist,
            'username': username
        }
        
        response = self._make_request(params)
        return response.get('artist') if response else None
    
    def get_album_info(self, artist: str, album: str, username: str) -> Optional[Dict[str, Any]]:
        """
        Get album information including user stats.
        
        Args:
            artist: Artist name
            album: Album name
            username: LastFM username
            
        Returns:
            Album info dictionary or None if error
        """
        params = {
            'method': 'album.getInfo',
            'artist': artist,
            'album': album,
            'username': username
        }
        
        response = self._make_request(params)
        return response.get('album') if response else None
    
    def is_track_playing(self, track_data: Dict[str, Any]) -> bool:
        """
        Check if a track is currently playing.
        
        Args:
            track_data: Track data from recent tracks API
            
        Returns:
            True if currently playing, False otherwise
        """
        return '@attr' in track_data and track_data['@attr'].get('nowplaying') == 'true'