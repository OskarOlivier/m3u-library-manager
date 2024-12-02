# core/services/service_base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Type, Any, Optional, Set
import logging
import yaml
from pathlib import Path

@dataclass
class ServiceConfig:
    """Configuration data for a service."""
    name: str
    enabled: bool = True
    settings: Dict[str, Any] = None
    dependencies: Set[str] = None

class ServiceState:
    """Represents service lifecycle state."""
    CREATED = "created"
    INITIALIZED = "initialized" 
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"

class ServiceProvider(ABC):
    """Base class for all application services."""
    
    def __init__(self, name: str):
        self.name = name
        self.state = ServiceState.CREATED
        self.config: Optional[ServiceConfig] = None
        self.logger = logging.getLogger(f'service.{name}')

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Called once at startup."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the service. May be called multiple times."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the service. May be called multiple times."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources. Called once at shutdown."""
        pass

class ServiceRegistry:
    """Manages service registration, configuration and lifecycle."""

    def __init__(self, config_path: Optional[Path] = None):
        self.services: Dict[str, ServiceProvider] = {}
        self.configs: Dict[str, ServiceConfig] = {}
        self.logger = logging.getLogger('service_registry')
        
        if config_path:
            self.load_configs(config_path)

    def load_configs(self, config_path: Path) -> None:
        """Load service configurations from YAML file."""
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            for service_name, config in config_data.get('services', {}).items():
                self.configs[service_name] = ServiceConfig(
                    name=service_name,
                    enabled=config.get('enabled', True),
                    settings=config.get('settings', {}),
                    dependencies=set(config.get('dependencies', []))
                )
        except Exception as e:
            self.logger.error(f"Failed to load service configs: {e}")
            raise

    def register(self, service: ServiceProvider) -> None:
        """Register a service with the registry."""
        if service.name in self.services:
            raise ValueError(f"Service {service.name} already registered")
            
        self.services[service.name] = service
        
        # Apply config if exists
        if service.name in self.configs:
            service.config = self.configs[service.name]

    async def start_services(self) -> None:
        """Initialize and start all services in dependency order."""
        started = set()
        
        async def start_service(name: str) -> None:
            if name in started:
                return
                
            service = self.services[name]
            config = self.configs.get(name)
            
            if config and config.dependencies:
                for dep in config.dependencies:
                    await start_service(dep)
                    
            try:
                await service.initialize()
                service.state = ServiceState.INITIALIZED
                
                await service.start()
                service.state = ServiceState.STARTED
                started.add(name)
                
            except Exception as e:
                service.state = ServiceState.ERROR
                self.logger.error(f"Failed to start {name}: {e}")
                raise

        # Start all registered services
        for name in self.services:
            await start_service(name)

    async def stop_services(self) -> None:
        """Stop all services in reverse dependency order."""
        for name, service in reversed(self.services.items()):
            try:
                await service.stop()
                service.state = ServiceState.STOPPED
            except Exception as e:
                service.state = ServiceState.ERROR
                self.logger.error(f"Failed to stop {name}: {e}")

    async def cleanup(self) -> None:
        """Clean up all services."""
        for name, service in reversed(self.services.items()):
            try:
                await service.cleanup()
            except Exception as e:
                self.logger.error(f"Failed to cleanup {name}: {e}")

class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass

class DependencyError(ServiceError):
    """Raised when service dependencies cannot be resolved."""
    pass

class ConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    pass