# Levels Module Migration Documentation

## Overview

The Levels module has been successfully migrated from a monolithic `levels.py` file to a modular structure. This migration improves code organization, maintainability, and follows the established pattern used by other modules in the project.

## New File Structure

```
levels/
├── __init__.py
├── helpers/
│   ├── __init__.py
│   ├── data_manager.py      # Levels and voice data persistence
│   ├── xp_manager.py        # XP calculation, leveling, and voice tracking
│   └── utils.py            # Utility functions and embed formatting
└── commands/
    ├── level.py            # Show individual user level stats
    ├── leveltop.py         # Level leaderboard with pagination
    ├── voicelevels.py      # Voice time leaderboard  
    └── setlevel.py         # Admin command to set user levels
```

## Module Components

### Main Module (`levels.py`)
- **Class**: `LevelsCog`
- **Functionality**: Main cog with event listeners and dynamic command loading
- **Features**: 
  - Handles XP gain from messages with anti-spam
  - Tracks voice channel time with periodic updates
  - Automatically discovers and loads all command modules
  - Proper setup/teardown functionality with task management

### Helper Modules

#### 1. Data Manager (`levels/helpers/data_manager.py`)
- **Class**: `LevelsDataManager`
- **Purpose**: Handles JSON data persistence for levels and voice tracking
- **Methods**:
  - `get_levels_data()` / `save_levels_data()` - Level data persistence
  - `get_voice_data()` / `save_voice_data()` - Voice data persistence  
  - `get_user_levels()` / `update_user_levels()` - Individual user level data
  - `get_user_voice()` / `add_voice_time()` - Individual user voice data
  - `ensure_user_exists()` - Initialize new users
- **Data Storage**: `data/levels.json` and `data/voice_levels.json`

#### 2. XP Manager (`levels/helpers/xp_manager.py`)
- **Class**: `XPManager`
- **Purpose**: Handles XP calculations, leveling logic, and voice tracking
- **Features**:
  - Anti-spam rate limiting (60 messages per minute)
  - Randomized XP gain (10-20 XP per message)
  - Level calculation (3500 XP per level)
  - Voice time tracking with session management
- **Methods**:
  - `add_xp()` - Add XP and check for level up
  - `calculate_level_progress()` - Progress calculation for embeds
  - `start_voice_tracking()` / `stop_voice_tracking()` - Voice session management
  - `save_all_voice_sessions()` - Periodic voice time updates
  - `set_user_level_from_messages()` - Admin level setting

#### 3. Utilities (`levels/helpers/utils.py`)
- **Purpose**: Formatting, embed creation, and data processing utilities
- **Key Functions**:
  - `create_progress_bar()` - Visual progress bars for embeds
  - `format_time()` - Convert seconds to readable time format
  - `create_level_embed()` - Standard level status embed
  - `create_leaderboard_embed()` - Formatted leaderboard display
  - `process_leaderboard_data()` - Sort and filter leaderboard data
  - `paginate_data()` - Handle pagination logic

### Command Modules

#### 1. Level Command (`levels/commands/level.py`)
- **Commands**: `-level`, `-xp`, `-lvl`, `-rank`
- **Purpose**: Display individual user level statistics
- **Features**:
  - Current level, XP, and total messages
  - Progress bar to next level
  - Voice time display
  - Works for self or other users

#### 2. Level Top Command (`levels/commands/leveltop.py`)
- **Commands**: `-leveltop`, `-lvltop`
- **Purpose**: Display level leaderboard with pagination
- **Features**:
  - Ranked by level then XP
  - 5 users per page with navigation buttons
  - Medal emojis for top 3 positions
  - Interactive pagination with timeout

#### 3. Voice Levels Command (`levels/commands/voicelevels.py`)
- **Commands**: `-voicelevels`, `-voicetop`, `-vtop`
- **Purpose**: Display voice time leaderboard
- **Features**:
  - Ranked by total voice time
  - 10 users per page with navigation
  - Formatted time display (days, hours, minutes)
  - Shared pagination system

#### 4. Set Level Command (`levels/commands/setlevel.py`)
- **Command**: `-setlevel` (Admin only)
- **Purpose**: Allow administrators to set user levels
- **Features**:
  - Set level based on message count
  - Automatic XP calculation
  - Permission checking and error handling
  - Comprehensive input validation

## Migration Benefits

1. **Improved Organization**: Each command has its own file, making the codebase easier to navigate
2. **Better Maintainability**: Isolated functionality allows for easier debugging and updates
3. **Code Reusability**: Helper modules prevent code duplication across commands
4. **Consistent Patterns**: Follows the same structure as other migrated modules
5. **Enhanced Performance**: Optimized voice tracking and data persistence
6. **Dynamic Loading**: Commands are automatically discovered and loaded

## Features Preserved

### XP System
- **Rate Limiting**: 60 messages per minute anti-spam
- **XP Gain**: 10-20 XP per message (randomized)
- **Level Calculation**: 3500 XP per level
- **Level Up Messages**: Automatic congratulatory embeds

### Voice Tracking
- **Real-time Monitoring**: Tracks users in voice channels
- **AFK Handling**: Excludes time spent in AFK channels
- **Periodic Updates**: Saves voice time every 60 seconds
- **Session Management**: Proper start/stop tracking

### Data Persistence
- **JSON Storage**: `data/levels.json` and `data/voice_levels.json`
- **Error Handling**: Graceful handling of corrupted files
- **Automatic Initialization**: Creates missing data structures

### Interactive Features
- **Pagination**: Navigation buttons for leaderboards
- **Progress Bars**: Visual XP progress indicators
- **Time Formatting**: Human-readable time displays
- **Error Embeds**: Consistent error messaging

## Leaderboard System

### Level Leaderboard
- **Sorting**: Primary by level, secondary by XP
- **Display**: Level, XP, and total messages
- **Pagination**: 5 users per page
- **Navigation**: Previous/Next buttons

### Voice Leaderboard  
- **Sorting**: By total voice time (descending)
- **Display**: Formatted time in days/hours/minutes
- **Pagination**: 10 users per page
- **Navigation**: Shared pagination system

### Shared Features
- **Medal System**: 🥇🥈🥉 for top 3 positions
- **Thumbnails**: First place user's avatar
- **Interactive**: Button navigation with user validation
- **Timeout**: 60-second interaction timeout

## Admin Features

### Set Level Command
- **Usage**: `setlevel @user message_count`
- **Permissions**: Administrator required
- **Calculation**: Automatic XP calculation from messages
- **Validation**: Input validation and error handling

## Error Handling

The module includes comprehensive error handling for:
- **Corrupted Data Files**: Automatic recovery and initialization
- **Missing Users**: Automatic user creation in database
- **Permission Errors**: Clear error messages for unauthorized access
- **Invalid Input**: Validation for admin commands
- **API Failures**: Graceful degradation for Discord API issues

## Data Structures

### Levels Data (`data/levels.json`)
```json
{
    "user_id": {
        "xp": 5250,
        "level": 1,
        "total_messages": 350,
        "last_message": 1699123456.789
    }
}
```

### Voice Data (`data/voice_levels.json`)
```json
{
    "user_id": {
        "voice_time": 7200.5
    }
}
```

## Performance Optimizations

1. **Batch Voice Updates**: Periodic saving instead of per-event
2. **Rate Limiting**: Built-in anti-spam protection
3. **Lazy Loading**: Commands loaded on-demand
4. **Efficient Pagination**: Optimized data processing for leaderboards
5. **Graceful Degradation**: Continues operation even with helper loading failures

This migration maintains 100% feature compatibility while significantly improving code organization, maintainability, and performance. The modular structure makes it easier to add new features, fix bugs, and maintain consistent behavior across all level-related functionality.