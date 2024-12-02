# core/context.py

from pathlib import Path
import logging
from typing import Dict, Type, Optional, Any, Callable
from core.events.event_bus import Event, EventType, EventBus
from core.events.event_service import EventService
from core.services.ui_service import UIService
from core.services.service_base import ServiceProvider, ServiceRegistry, ServiceConfig
from core.cache.relationship_cache import RelationshipCache
from core.matching.window_handler import WindowHandler
from core.matching.song_matcher import SongMatcher
from core.playlist.playlist_manager import PlaylistManager
from core.sync.ssh_handler import SSHHandler, SSHCredentials
from core.sync.file_comparator import FileComparator
from core.sync.sync_operations import SyncOperations
from core.sync.backup_manager import BackupManager
from core.state.state_service import StateService
from core.services.analysis_service import AnalysisService
from app.config import Config

class WindowService(ServiceProvider):
    """Manages window-related services."""
    def __init__(self):
        super().__init__("window_service")
        self.window_handler = WindowHandler()
        self.song_matcher = SongMatcher()
        self.logger = logging.getLogger('window_service')
        
    async def initialize(self) -> None:
        """Initialize the window service."""
        self.logger.debug("Initializing window service")
        if self.config:
            poll_interval = self.config.settings.get('poll_interval', 1000)
            self.window_handler.set_poll_interval(poll_interval)
        
    async def start(self) -> None:
        """Start the window service."""
        self.logger.debug("Starting window service")
        
    async def stop(self) -> None:
        """Stop the window service."""
        self.logger.debug("Stopping window service")
        self.window_handler.cleanup()
        
    def cleanup(self):
        """Clean up resources."""
        self.logger.debug("Cleaning up window service")
        if self.window_handler:
            self.window_handler.cleanup()

class PlaylistService(ServiceProvider):
    """Manages playlist-related services."""
    def __init__(self):
        super().__init__("playlist_service")
        self.playlist_manager = PlaylistManager(
            Path(Config.LOCAL_BASE),
            Path(Config.PLAYLISTS_DIR),
            Path(Config.BACKUP_DIR)
        )
        self.backup_manager = BackupManager(Path(Config.BACKUP_DIR))
        self.logger = logging.getLogger('playlist_service')
        
    async def initialize(self) -> None:
        """Initialize the playlist service."""
        self.logger.debug("Initializing playlist service")
            
    async def start(self) -> None:
        """Start the playlist service."""
        self.logger.debug("Starting playlist service")
        pass
        
    async def stop(self) -> None:
        """Stop the playlist service."""
        self.logger.debug("Stopping playlist service")
        pass

class SyncService(ServiceProvider):
    """Manages synchronization services."""
    def __init__(self):
        super().__init__("sync_service")
        self.ssh_handler: Optional[SSHHandler] = None
        self.file_comparator: Optional[FileComparator] = None
        self.sync_ops: Optional[SyncOperations] = None
        self.logger = logging.getLogger('sync_service')
        
    async def initialize(self) -> None:
        """Initialize the sync service."""
        self.logger.debug("Initializing sync service")
        if self.config:
            self.connection_timeout = self.config.settings.get('connection_timeout', 30)
            self.retry_attempts = self.config.settings.get('retry_attempts', 3)
            
    async def start(self) -> None:
        """Start the sync service."""
        self.logger.debug("Starting sync service")
        pass
        
    async def stop(self) -> None:
        """Stop the sync service."""
        self.logger.debug("Stopping sync service")
        if self.ssh_handler:
            self.ssh_handler = None
            
    def initialize_connection(self, credentials: SSHCredentials) -> bool:
        """Initialize SSH connection with credentials."""
        try:
            self.ssh_handler = SSHHandler(credentials)
            success, error = self.ssh_handler.test_connection()
            
            if success:
                self.file_comparator = FileComparator(self.ssh_handler)
                self.sync_ops = SyncOperations(
                    self.ssh_handler,
                    PlaylistService().backup_manager,
                    Path(Config.LOCAL_BASE),
                    Config.SSH_REMOTE_PATH
                )
                return True
            return False
            
        except Exception:
            return False

# core/context.py

class ApplicationContext:
    """Central manager for application services and state."""
    
    _instance = None
    
    def __init__(self):
        if ApplicationContext._instance is not None:
            raise RuntimeError("ApplicationContext is a singleton")
            
        self.logger = logging.getLogger('application_context')
        
        # Initialize core services
        self.event_service = EventService()
        self.event_bus = EventBus.get_instance()
        self._cache = RelationshipCache.get_instance()
        self.state_service = StateService()
        self.ui_service = UIService()
        self.analysis_service = AnalysisService()
        
        # Track initialization state
        self._initialization_complete = False
        self._initialization_error = None
        
        # Initialize service registry
        config_path = Path("config/services.yaml")
        self.registry = ServiceRegistry(config_path)
        
        # Register core services EXCEPT relationship cache
        self._register_core_services()
        
        self._connect_event_bus()

    async def initialize(self, playlists_dir: Path) -> None:
        """Initialize application context."""
        if self._initialization_complete:
            self.logger.warning("Context already initialized")
            return

        try:
            self.logger.info("Starting ApplicationContext initialization")
            
            # Initialize cache first
            if not self._cache.is_initialized:
                self.logger.info("Initializing relationship cache...")
                await self._cache.initialize(playlists_dir)
            
            # Then start all other services
            await self.registry.start_services()
            
            # Initialize state service after cache
            await self.state_service.initialize()
            
            self._initialization_complete = True
            self._initialization_error = None
            
            self.logger.info("ApplicationContext initialization complete")
            self.event_bus.emit_event("context_initialized", {
                "status": "success"
            })
                
        except Exception as e:
            self._initialization_error = str(e)
            self.logger.error(f"Context initialization failed: {e}", exc_info=True)
            raise
            
    def _register_core_services(self):
        """Register all core services with the registry."""
        services = [
            ("window_service", WindowService()),
            ("playlist_service", PlaylistService()),
            ("sync_service", SyncService()),
            ("ui_service", self.ui_service),
            ("event_service", self.event_service),
            ("state_service", self.state_service),
            ("analysis_service", self.analysis_service)
            # Removed relationship_cache from service registry
        ]
        
        for name, service in services:
            self.registry.register(service)
        
    @property
    def cache(self) -> RelationshipCache:
        """Get the relationship cache instance."""
        return self._cache
        
    @classmethod
    def get_instance(cls) -> 'ApplicationContext':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = ApplicationContext()
        return cls._instance
        
    def is_initialized(self) -> bool:
        """Check if context is fully initialized."""
        return self._initialization_complete

    def get_initialization_error(self) -> Optional[str]:
        """Get any initialization error that occurred."""
        return self._initialization_error

    async def ensure_initialized(self, playlists_dir: Path) -> bool:
        """Ensure context is initialized, initializing if necessary."""
        if not self.is_initialized:
            try:
                await self.initialize(playlists_dir)
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize context: {e}")
                return False
        return True
        
    def _connect_event_bus(self):
        """Connect old event bus to new event service."""
        self.event_bus.event_occurred.connect(
            lambda event: self.event_service.emit_event(event.type, event.data)
        )
        
    def get_service(self, service_type: Type[ServiceProvider]) -> ServiceProvider:
        """Get a service instance from the registry."""
        service_name = service_type().name  # Get name from temporary instance
        service = self.registry.services.get(service_name)
        if not service:
            service = service_type()
            self.registry.register(service)
        return service
        
    def show_error(self, title: str, message: str):
        """Helper method for showing error dialogs."""
        self.ui_service.show_error(title, message)
            
    def confirm_operation(self, title: str, message: str, dangerous: bool = False) -> bool:
        """Helper method for operation confirmations."""
        return self.ui_service.confirm_operation(title, message, dangerous)
            
    def subscribe_event(self, event_type: str, callback: callable, 
                       priority: Optional[int] = None,
                       filter_fn: Optional[callable] = None) -> None:
        """Subscribe to application events with the enhanced event service."""
        if priority is not None:
            from core.events.event_service import EventPriority
            priority_map = {
                0: EventPriority.LOW,
                1: EventPriority.NORMAL,
                2: EventPriority.HIGH,
                3: EventPriority.CRITICAL
            }
            event_priority = priority_map.get(priority, EventPriority.NORMAL)
        else:
            from core.events.event_service import EventPriority
            event_priority = EventPriority.NORMAL
            
        self.event_service.subscribe(event_type, callback, event_priority, filter_fn)

    def register_state(self, state_id: str, state_class: Type, **kwargs) -> Any:
        """Register a new state with the state service."""
        return self.state_service.register_state(state_id, state_class, **kwargs)

    def get_state(self, state_id: str) -> Optional[Any]:
        """Get a registered state instance."""
        return self.state_service.get_state(state_id)
        
    async def analyze_playlist(self, playlist_path: Path, 
                             progress_callback: Optional[Callable[[int], None]] = None):
        """Helper method for playlist analysis."""
        return await self.analysis_service.analyze_playlist(playlist_path, progress_callback)
        
    async def cleanup(self) -> None:
        """Clean up all services and states."""
        try:
            self.logger.info("Starting ApplicationContext cleanup")
            
            # Save states before cleanup
            self.state_service.save_all_states()
            
            # Stop all services in reverse dependency order
            await self.registry.stop_services()
            
            # Clean up services
            await self.registry.cleanup()
            
            # Reset initialization state
            self._initialization_complete = False
            self._initialization_error = None
            
            self.logger.info("ApplicationContext cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Context cleanup failed: {e}", exc_info=True)
            raise