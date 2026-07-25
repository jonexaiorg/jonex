"""ParserRegistry — Callable-based extension-to-parser routing.

Unifies parser registration and route lookup in a single layer.
Handlers are stored as Callable objects (not strings), so IDE
refactoring tools can track references.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class ParserRoute:
    """A single route: N extensions → one Callable handler + optional fallback."""

    extensions: List[str]
    handler: Callable
    fallback: Optional[Callable] = None

    def matches(self, ext: str) -> bool:
        return "*" in self.extensions or ext in self.extensions


class ParserRegistry:
    """Declarative registry mapping file extensions to parser Callables.

    Usage:
        registry = ParserRegistry()
        registry.register([".pdf"], Parser.parse_pdf)
        registry.register([".jpg", ".png"], Parser.parse_image,
                          fallback=MineruParser().parse_image)
        route = registry.lookup(".pdf")
    """

    def __init__(self):
        self._routes: List[ParserRoute] = []

    def register(
        self,
        extensions: List[str],
        handler: Callable,
        fallback: Optional[Callable] = None,
    ) -> None:
        self._routes.append(ParserRoute(extensions, handler, fallback))

    def lookup(self, ext: str) -> Optional[ParserRoute]:
        ext = ext.lower()
        for route in self._routes:
            if route.matches(ext):
                return route
        return None

    def get_catch_all(self) -> Optional[ParserRoute]:
        for route in self._routes:
            if "*" in route.extensions:
                return route
        return None

    def __iter__(self):
        return iter(self._routes)

    def __len__(self) -> int:
        return len(self._routes)


# Backward compatibility aliases
ExtensionRouter = ParserRegistry
RouteEntry = ParserRoute
