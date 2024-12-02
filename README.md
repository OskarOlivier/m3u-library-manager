README for m3u-library-manager
m3u-library-manager
Version: 0.1
License: MIT

Overview

m3u-library-manager is a Python-based tool for managing music libraries and playlists. It provides features for playlist creation, management, backup, and synchronization across local and remote storage. This application also incorporates audio analysis capabilities and an intuitive user interface for seamless interactions.

Key Features

Core Functionalities:
Playlist Management:
Create, read, modify, and delete .m3u playlists.
Toggle song inclusion in playlists based on normalized paths.
Identify duplicate tracks and perform safety operations like backup creation.

Cache Management:
Optimize performance with caching of playlist relationships and data.
Singleton cache management for ensuring data consistency and efficient access.

Synchronization:
Compare and synchronize music files between local and remote libraries.
Robust SSH integration for secure remote file operations.

Search and Matching:
Match songs to filenames and playlist entries using normalized path matching and string similarity estimation.
Support for fuzzy matching for enhanced search capabilities.

Backup and Restore:
Automatic and manual playlist backup system.
Keep backups and restore playlists when needed.

Architecture

Modular Design:
The project is organized into distinct modules for maintainability and scalability:

app/: Handles configuration and application-wide settings.
core/: Contains the primary logic for cache management, playlist operations, analysis, synchronization, and event handling.
utils/: Provides utility functions for file and path handling, parsing .m3u playlists, and ID3 tag operations.
gui/: Interface implementation

Dependencies

PyQt6: GUI integration and event handling.
asyncio: Asynchronous operations for file I/O and SSH tasks.
Levenshtein: String similarity calculations.
psutil: System-level process management.
win32gui & win32process: Window detection and interaction on Windows.

Roadmap
Upcoming Features:
Enhanced GUI with drag-and-drop playlist editing.
Real-time playlist synchronization with remote storage.
Audio Analysis for BPM detection
