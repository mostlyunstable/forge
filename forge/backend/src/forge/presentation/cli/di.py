"""Dependency injection container for the CLI."""

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    def __init__(self) -> None:
        self._providers: dict[type, Callable[[], Any]] = {}
        self._instances: dict[type, Any] = {}

    def register(self, interface: type[T], provider: Callable[[], T]) -> None:
        """Register a provider function for an interface."""
        self._providers[interface] = provider

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        self._instances[interface] = instance

    def resolve(self, interface: type[T]) -> T:
        """Resolve an instance for the given interface."""
        from typing import cast
        if interface in self._instances:
            return cast(T, self._instances[interface])

        if interface in self._providers:
            instance = self._providers[interface]()
            self._instances[interface] = instance
            return cast(T, instance)

        raise ValueError(f"No provider registered for {interface}")


# Global container instance for the CLI
cli_container = Container()
