# M3U Library Manager Documentation

## Overview
The M3U Library Manager is a tool for managing music playlists with a focus on maintaining playlist health and metadata integrity. It provides features for playlist management, song matching, and metadata analysis/cleanup.

## Core Components

### Playlist Management
- **Playlist Operations**: Basic operations for reading, writing, and validating M3U playlists
- **Song Matching**: Matches currently playing songs with filesystem locations and playlists
- **Playlist Health**: Analyzes playlists for missing files, invalid paths, and incomplete metadata

### Analysis & Cleanup
- **BPM Analysis**: Detects and updates BPM metadata in MP3 files
- **ID3 Tag Management**: Ensures consistent and complete metadata across the library
- **File Safety**: Implements safeguards against file corruption and metadata loss

### User Interface
- **Playlist Manager Window**: 
  - Shows all playlists at once
  - Displays current song and its presence in playlists
  - Presents playlist health and cleanup options
  - Accessible via global hotkey (Ctrl+Alt+P)

## Future Features

### Sync Operations
- Remote playlist directory synchronization
- Bidirectional sync capabilities
- Conflict resolution

### Dynamic Playlists
- Rule-based playlist generation
- Smart playlist updates

## Technical Details

### File Safety Features (Planned)
- Temporary file handling for safe writes
- ID3 tag version preservation
- Backup creation before modifications
- Verification of writes and changes
- Rollback capabilities for failed operations

### Dependencies
```
PyQt6        # GUI Framework
keyboard     # Hotkey support
mutagen      # MP3/ID3 tag handling
numpy        # Audio analysis
win32gui     # Window title detection
```

### Project Structure
```
m3u_library_manager/
ÃÄÄ core/
³   ÃÄÄ analysis/          # Audio analysis components
³   ³   ÀÄÄ bpm_analyzer.py
³   ÃÄÄ matching/          # Song matching functionality
³   ÀÄÄ playlist/          # Playlist operations
ÃÄÄ gui/                   # User interface components
³   ÀÄÄ windows/          
ÃÄÄ operations/            # High-level operations
³   ÃÄÄ analysis_ops/     
³   ÀÄÄ playlist_ops/     
ÀÄÄ utils/                 # Utility functions
    ÃÄÄ audio/
    ÃÄÄ id3/
    ÀÄÄ m3u/
```

## Usage Flows

### Playlist Health Check
1. User selects playlist in manager
2. System analyzes:
   - Missing files
   - Invalid paths
   - Incomplete metadata (BPM, etc.)
3. Presents cleanup options if issues found

### Metadata Cleanup
1. Detects files with missing/incorrect metadata
2. Offers analysis options (BPM detection, etc.)
3. Safely updates ID3 tags with new information
4. Verifies changes and reports results

### Current Song Management
1. Detects currently playing song from window title
2. Locates matching files in filesystem
3. Shows containing playlists
4. Enables quick playlist add/remove operations

## Development Guidelines
- Always implement safety checks for file operations
- Maintain clear separation between core operations and UI
- Provide progress feedback for long-running operations
- Include error handling and user feedback
- Keep operations interruptible where appropriate
