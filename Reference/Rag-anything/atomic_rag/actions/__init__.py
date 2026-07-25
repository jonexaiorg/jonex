"""Action registry for dispatching invoke actions."""

from typing import Awaitable, Callable, Optional


class ActionRegistry:
    """Registry mapping action names to async handler functions."""

    _handlers: dict = {}

    @classmethod
    def register(cls, name: str):
        """Decorator: register an async handler for the given action name."""
        def decorator(f: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
            cls._handlers[name] = f
            return f
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Callable[..., Awaitable]]:
        """Get the registered handler for an action name, or None."""
        return cls._handlers.get(name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered handlers (useful in tests)."""
        cls._handlers.clear()
