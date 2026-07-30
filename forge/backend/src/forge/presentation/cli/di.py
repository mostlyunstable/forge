"""Dependency injection container for the CLI."""

from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")

class Container:
    def __init__(self):
        self._providers: Dict[Type, Callable[[], Any]] = {}
        self._instances: Dict[Type, Any] = {}

    def register(self, interface: Type[T], provider: Callable[[], T]) -> None:
        """Register a provider function for an interface."""
        self._providers[interface] = provider

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        self._instances[interface] = instance

    def resolve(self, interface: Type[T]) -> T:
        """Resolve an instance for the given interface."""
        if interface in self._instances:
            return self._instances[interface]
        
        if interface in self._providers:
            instance = self._providers[interface]()
            self._instances[interface] = instance
            return instance
            
        raise ValueError(f"No provider registered for {interface}")

# Global container instance for the CLI
cli_container = Container()
