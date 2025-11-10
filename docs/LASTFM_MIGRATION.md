# LastFM Module Migration Documentation

## Overview

The LastFM module has been successfully migrated from a monolithic `lastfm.py` file to a modular structure. This migration improves code organization, maintainability, and follows the established pattern used by other modules in the project.

## New File Structure

```
lastfm/
├── __init__.py
├── helpers/
│   ├── __init__.py
│   ├── data_manager.py      # LastFM account linking and data persistence
│   ├── api_client.py        # LastFM API wrapper and request handling
│   └── utils.py            # Utility functions and embed formatting
└── commands/
    ├── login.py            # Link LastFM account command
    ├── profile.py          # Show LastFM profile command (aliases: lastfm, lf, me, p)
    ├── now_playing.py      # Show currently playing track command (np)
    ├── server_now_playing.py  # Show all server playing tracks command (snp)
    └── logout.py           # Unlink LastFM account command
```

## Module Components

### Main Module (`lastfm.py`)
- **Class**: `LastFMCog`
- **Functionality**: Main cog with dynamic command loading
- **Features**: 
  - Automatically discovers and loads all command modules
  - Proper setup/teardown functionality
  - Error handling for failed command loading

### Helper Modules

#### 1. Data Manager (`lastfm/helpers/data_manager.py`)
- **Class**: `LastFMDataManager`
- **Purpose**: Handles JSON data persistence for user account linking
- **Methods**:
  - `link_user(user_id, lastfm_username)` - Link Discord user to LastFM account
  - `get_lastfm_username(user_id)` - Get LastFM username for Discord user
  - `unlink_user(user_id)` - Remove user's LastFM link
  - `get_all_accounts()` - Get all linked accounts
- **Data Storage**: `data/lastfm.json`

#### 2. API Client (`lastfm/helpers/api_client.py`)
- **Class**: `LastFMAPIClient`
- **Purpose**: Wrapper for LastFM Web API interactions
- **Features**:
  - Centralized API key management from environment variables
  - Error handling with custom `LastFMAPIError` exception
  - Rate limiting and request validation
- **Methods**:
  - `get_user_info(username)` - Fetch user profile information
  - `get_recent_tracks(username, limit)` - Get recent/current tracks
  - `get_track_info(artist, track, username)` - Get track details with user stats
  - `get_artist_info(artist, username)` - Get artist details with user stats
  - `get_album_info(artist, album, username)` - Get album details with user stats

#### 3. Utilities (`lastfm/helpers/utils.py`)
- **Purpose**: Formatting, validation, and embed creation utilities
- **Key Functions**:
  - `create_lastfm_embed()` - Standard LastFM themed embeds
  - `format_user_profile_embed()` - Format user profile display
  - `format_now_playing_embed()` - Format currently playing track
  - `format_server_now_playing_embed()` - Format server-wide playing list
  - `create_not_linked_embed()` - Error message for unlinked accounts
  - `safe_get_scrobble_count()` - Safe extraction of scrobble statistics

### Command Modules

#### 1. Login Command (`lastfm/commands/login.py`)
- **Command**: `-login [username]`
- **Purpose**: Link Discord account to LastFM profile
- **Features**: Success confirmation with embed

#### 2. Profile Command (`lastfm/commands/profile.py`)
- **Commands**: `-lastfm`, `-lf`, `-profile`, `-me`, `-p`
- **Purpose**: Display user's LastFM profile statistics
- **Features**:
  - Total scrobbles and registration date
  - Profile avatar and clickable links
  - Optional track count display

#### 3. Now Playing Command (`lastfm/commands/now_playing.py`)
- **Command**: `-np`
- **Purpose**: Show currently playing track
- **Features**:
  - Real-time playing status detection
  - Album artwork thumbnails
  - Detailed scrobble statistics (artist/album/track/total)
  - Clickable links to LastFM pages

#### 4. Server Now Playing Command (`lastfm/commands/server_now_playing.py`)
- **Commands**: `-servernowplaying`, `-snp`
- **Purpose**: Show all currently playing tracks in the server
- **Features**:
  - Aggregates all linked users' current tracks
  - User and track count summary
  - Clickable links for users and tracks

#### 5. Logout Command (`lastfm/commands/logout.py`)
- **Command**: `-logout`
- **Purpose**: Unlink LastFM account from Discord
- **Features**: Confirmation and error handling

## Migration Benefits

1. **Improved Organization**: Each command has its own file, making the codebase easier to navigate
2. **Better Maintainability**: Isolated functionality allows for easier debugging and updates
3. **Code Reusability**: Helper modules can be reused across different commands
4. **Consistent Patterns**: Follows the same structure as other migrated modules
5. **Error Isolation**: Issues in one command don't affect others
6. **Dynamic Loading**: Commands are automatically discovered and loaded

## Environment Requirements

- **Environment Variable**: `lastfm_key` - LastFM API key
- **Dependencies**: `discord.py`, `requests`, `python-dotenv`
- **Data Directory**: `data/` folder for JSON persistence

## Usage Examples

```python
# Link account
-login myLastFMUsername

# View profile (multiple aliases)
-lastfm
-lf
-profile
-me
-p

# Check what's playing
-np

# See server activity
-servernowplaying
-snp

# Unlink account
-logout
```

## Error Handling

The module includes comprehensive error handling for:
- Missing LastFM account links
- API request failures
- Invalid usernames
- Network connectivity issues
- Malformed API responses

## Data Persistence

User account links are stored in `data/lastfm.json` with the format:
```json
{
    "discord_user_id": "lastfm_username",
    "123456789": "john_music_lover"
}
```

## API Integration

The module integrates with the following LastFM API endpoints:
- `user.getInfo` - User profile data
- `user.getRecentTracks` - Recent and current tracks
- `track.getInfo` - Track-specific data with user stats
- `artist.getInfo` - Artist-specific data with user stats  
- `album.getInfo` - Album-specific data with user stats

This migration maintains 100% feature compatibility while significantly improving code organization and maintainability.