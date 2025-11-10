# BlockedTerms Migration Documentation

## Overview

This document outlines the migration of `blockedterms.py` from a monolithic file structure to a modular organization for better code readability, maintainability, and organization.

## Migration Goal

Transform the blockedterms module from a single large file into a structured directory with:
- Individual files for each command
- Shared helper utilities
- Centralized data management
- Auto-moderation system separation

## Before Migration

### Original Structure
```
blockedterms.py (~400 lines)
├── BlockedTermsCog class
├── blockterm command
├── unblockterm command 
├── blockedterms command (list)
├── Auto-moderation message listener
├── Text normalization utilities
├── Direct JSON file manipulation
└── Inline punishment logic
```

### Issues with Original Structure
- All functionality mixed in single file
- Difficult to locate specific command logic
- Helper functions scattered throughout
- Data management coupled with command logic
- Hard to test individual components

## After Migration

### New Modular Structure
```
blockedterms/
├── helpers/
│   ├── __init__.py
│   ├── data_manager.py      # Centralized JSON operations
│   ├── utils.py             # Text normalization utilities
│   └── punishment_manager.py # Punishment application logic
├── commands/
│   ├── add_term.py          # blockterm command
│   ├── remove_term.py       # unblockterm command
│   └── list_terms.py        # blockedterms command
├── moderation/
│   └── automod.py           # Auto-moderation message listener
└── blockedterms.py          # Main cog with dynamic loading
```

## Key Components

### Helper Modules

#### `helpers/data_manager.py`
- **Purpose**: Centralized blocked terms data management
- **Key Functions**:
  - `load_blocked_terms()`: Load terms from JSON
  - `save_blocked_terms()`: Save terms to JSON
  - `add_blocked_term()`: Add new blocked term
  - `remove_blocked_term()`: Remove existing term
  - `term_exists()`: Check if term exists

#### `helpers/utils.py`
- **Purpose**: Text processing and normalization utilities
- **Key Functions**:
  - `normalize_text()`: Remove accents and normalize text
  - `remove_accents()`: Remove diacritical marks
  - `contains_blocked_term()`: Check if text contains blocked terms

#### `helpers/punishment_manager.py`
- **Purpose**: Handle punishment application for blocked terms
- **Key Functions**:
  - `apply_punishment()`: Apply appropriate punishment
  - `get_punishment_for_term()`: Get punishment level for specific term
  - `log_punishment()`: Log punishment actions

### Command Modules

#### `commands/add_term.py`
- **Purpose**: Handle adding new blocked terms
- **Command**: `!blockterm <term> [punishment_level]`
- **Features**: Validation, duplicate checking, punishment level setting

#### `commands/remove_term.py`
- **Purpose**: Handle removing blocked terms
- **Command**: `!unblockterm <term>`
- **Features**: Existence checking, confirmation, cleanup

#### `commands/list_terms.py`
- **Purpose**: Display all blocked terms
- **Command**: `!blockedterms`
- **Features**: Paginated display, formatting, term count

### Moderation Module

#### `moderation/automod.py`
- **Purpose**: Auto-moderation message listener
- **Features**: Real-time message scanning, punishment application, logging

### Main Cog

#### `blockedterms.py`
- **Purpose**: Main cog that loads all components
- **Features**: Dynamic command loading, event listener registration, error handling

## Benefits of Migration

### Code Organization
- ✅ Each command in its own file
- ✅ Shared utilities in helpers
- ✅ Clear separation of concerns
- ✅ Easy to locate specific functionality

### Maintainability
- ✅ Centralized data management
- ✅ Reusable helper functions
- ✅ Consistent error handling
- ✅ Easier testing and debugging

### Scalability
- ✅ Easy to add new commands
- ✅ Helper functions can be extended
- ✅ Modular structure supports growth
- ✅ Clear patterns for future development

### Code Quality
- ✅ Reduced code duplication
- ✅ Single responsibility principle
- ✅ Better error handling
- ✅ Improved documentation

## Migration Process

1. **Analysis**: Identified all functions and their dependencies
2. **Structure Creation**: Created directory structure with logical groupings
3. **Helper Extraction**: Moved shared utilities to helpers/ directory
4. **Command Migration**: Converted each command to individual files
5. **Data Management**: Centralized JSON operations in data_manager
6. **Auto-moderation**: Separated message listener into moderation/ module
7. **Main Cog**: Created new blockedterms.py with dynamic loading
8. **Testing**: Verified all functionality works with new structure

## Usage After Migration

The migrated blockedterms module maintains the same external interface:

```python
# Commands work exactly the same
!blockterm badword 2
!unblockterm badword
!blockedterms

# Auto-moderation continues to work automatically
# Punishments are applied as configured
# All data is preserved in the same JSON format
```

## File Mapping

| Original Location | New Location | Purpose |
|------------------|--------------|---------|
| `BlockedTermsCog.blockterm` | `commands/add_term.py` | Add blocked term command |
| `BlockedTermsCog.unblockterm` | `commands/remove_term.py` | Remove blocked term command |
| `BlockedTermsCog.blockedterms` | `commands/list_terms.py` | List blocked terms command |
| `BlockedTermsCog.on_message` | `moderation/automod.py` | Auto-moderation listener |
| Inline data operations | `helpers/data_manager.py` | Centralized data management |
| Text utilities | `helpers/utils.py` | Text processing functions |
| Punishment logic | `helpers/punishment_manager.py` | Punishment application |

## Technical Notes

- All imports updated to use relative imports within blockedterms package
- Data file paths remain the same (data/blockedterms.json, data/punishments.json)
- Error handling improved with centralized patterns
- Logging maintained for all operations
- Performance characteristics unchanged

## Consistency with Other Migrations

This migration follows the same patterns established in:
- Admin module migration (admin/ directory)
- Birthday module migration (birthday/ directory)

The consistent structure makes the entire codebase more predictable and maintainable.