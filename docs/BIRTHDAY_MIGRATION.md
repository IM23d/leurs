# Birthday Module Migration

This document outlines the migration of birthday.py from a single large file to a modular structure for better maintainability and readability.

## Migration Overview

The original `birthday.py` file (now backed up as `birthday_old.py`) contained birthday management functionality and message snipe functionality. This has been restructured into a modular system while maintaining all original functionality.

## New Directory Structure

```
birthday/
├── helpers/
│   ├── __init__.py
│   ├── data_manager.py      # Birthday data management
│   ├── utils.py             # Birthday utility functions
│   └── snipe_manager.py     # Message snipe management (unused in final version)
├── commands/
│   ├── view.py             # View birthday command
│   ├── set.py              # Set birthday command
│   └── list.py             # List birthdays command
└── snipe/
    ├── snipe.py            # Snipe command
    └── clear.py            # Clear snipe command
```

## Migrated Commands

### Birthday Commands (Group: `bday`)
- **bday** - View your own or another user's birthday
- **bday set** - Set your birthday (format: DD-MM-YYYY or DD.MM.YYYY)
- **bday list** - List upcoming birthdays in the server (top 10)

### Snipe Commands
- **s** - Show the most recently deleted message in the channel
- **cs** - Clear all stored deleted messages for the current channel

## Helper Components

### BirthdayDataManager (`birthday/helpers/data_manager.py`)
Centralized birthday data management with methods for:
- Loading and saving birthday data from JSON
- Setting, getting, and removing user birthdays
- Managing the birthdays.json file

### Birthday Utils (`birthday/helpers/utils.py`)
Birthday-specific utilities including:
- Date calculation functions (`get_next_birthday_timestamp`, `calculate_next_age`, `get_next_birthday_date`)
- Date validation (`validate_birthday_date`)
- Embed helpers (`create_error_embed`, `create_success_embed`, `create_info_embed`)

### SnipeManager (`birthday/helpers/snipe_manager.py`)
Message deletion tracking with methods for:
- Storing deleted message data
- Automatic cleanup of old messages
- Retrieving and clearing snipe data

## Key Features Preserved

1. **Birthday Functionality**:
   - Support for DD-MM-YYYY and DD.MM.YYYY date formats
   - Validation for future dates and invalid years
   - Discord timestamp formatting for relative dates
   - Age calculation for next birthday
   - Server-wide birthday listing with sorting

2. **Snipe Functionality**:
   - Tracking deleted messages for 2 hours
   - Support for text content, attachments, and embeds
   - Image attachment preview in snipe embeds
   - Automatic cleanup of old data
   - Channel-specific message clearing

## Migration Benefits

1. **Maintainability**: Each command is now in its own focused file
2. **Readability**: Cleaner separation of concerns
3. **Modularity**: Commands can be modified independently
4. **Reusability**: Helper functions are centralized and reusable
5. **Testing**: Individual components can be tested in isolation

## Implementation Details

The new birthday.py file uses a hybrid approach:
- Core functionality is embedded directly in the main cog class
- Helper functions are imported dynamically when needed
- This maintains compatibility while organizing the code better

## Command Structure

### Birthday Commands
```
bday                    # View birthday (your own or mention someone)
bday set 31-12-2000     # Set birthday
bday list               # List upcoming birthdays
```

### Snipe Commands
```
s                       # Show last deleted message
cs                      # Clear stored deleted messages for channel
```

## Data Storage

- **Birthday Data**: Stored in `data/birthdays.json`
- **Snipe Data**: Stored in memory with 2-hour retention
- **Format**: Birthdays stored as DD-MM-YYYY strings

## Error Handling

- Standardized error messages with Discord embeds
- Input validation for date formats
- Graceful handling of missing data
- Proper permission and existence checks

## Compatibility

- All original commands work exactly the same
- Same command names and syntax
- Same data storage format
- Same permissions and restrictions

## Testing

After migration, verify:
1. Birthday setting and viewing works correctly
2. Date validation catches invalid inputs
3. Birthday list shows correct upcoming dates
4. Snipe functionality tracks deleted messages
5. Automatic cleanup of old snipe data works
6. All embeds display correctly

## Rollback

If issues occur, restore original functionality by:
1. Renaming `birthday.py` to `birthday_new.py`
2. Renaming `birthday_old.py` back to `birthday.py`
3. Removing the `birthday/` directory
4. Restarting the bot

This migration maintains all functionality while providing a much cleaner and more maintainable codebase structure.