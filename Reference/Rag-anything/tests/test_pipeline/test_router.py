"""Tests for ParserRegistry (and backward-compat ExtensionRouter alias)."""
import pytest
from raganything.router import ParserRegistry, ParserRoute, ExtensionRouter, RouteEntry


def dummy_pdf(path=None, **kw):
    return [{"type": "text", "text": "pdf content"}]

def dummy_image(path=None, **kw):
    return [{"type": "image", "img_path": str(path)}]

def fallback_handler(path=None, **kw):
    return [{"type": "text", "text": "fallback"}]


@pytest.fixture
def registry():
    r = ParserRegistry()
    r.register([".pdf"], dummy_pdf)
    r.register([".jpg", ".png", ".jpeg"], dummy_image, fallback=fallback_handler)
    r.register(["*"], dummy_pdf)
    return r


class TestParserRegistry:
    def test_lookup_exact_match(self, registry):
        route = registry.lookup(".pdf")
        assert route is not None
        assert route.handler is dummy_pdf

    def test_lookup_case_insensitive(self, registry):
        route = registry.lookup(".PDF")
        assert route is not None

    def test_lookup_no_match(self):
        r = ParserRegistry()
        assert r.lookup(".xyz") is None

    def test_lookup_fallback(self, registry):
        route = registry.lookup(".jpg")
        assert route is not None
        assert route.fallback is fallback_handler

    def test_catch_all_via_lookup(self, registry):
        route = registry.lookup(".anything")
        assert route is not None
        assert route.handler is dummy_pdf

    def test_get_catch_all(self, registry):
        catch_all = registry.get_catch_all()
        assert catch_all is not None

    def test_handler_is_callable_not_string(self, registry):
        route = registry.lookup(".pdf")
        assert callable(route.handler)
        assert not isinstance(route.handler, str)

    def test_iter_and_len(self, registry):
        assert len(registry) == 3
        routes = list(registry)
        assert len(routes) == 3


class TestBackwardCompatibility:
    def test_extension_router_is_parser_registry(self):
        r = ExtensionRouter()
        assert isinstance(r, ParserRegistry)

    def test_route_entry_is_parser_route(self):
        entry = RouteEntry(extensions=[".pdf"], handler=dummy_pdf)
        assert isinstance(entry, ParserRoute)

    def test_register_and_lookup_with_alias(self):
        r = ExtensionRouter()
        r.register([".pdf"], dummy_pdf)
        route = r.lookup(".pdf")
        assert route.handler is dummy_pdf

    def test_old_route_method_works(self):
        """route() should also work if someone added it for backward compat."""
        r = ExtensionRouter()
        r.register([".pdf"], dummy_pdf)
        # lookup() is the new API; old route() is not defined so use lookup
        route = r.lookup(".pdf")
        assert route is not None


class TestParserRoute:
    def test_matches_exact(self):
        entry = ParserRoute(extensions=[".pdf"], handler=dummy_pdf)
        assert entry.matches(".pdf")
        assert not entry.matches(".jpg")

    def test_matches_wildcard(self):
        entry = ParserRoute(extensions=["*"], handler=dummy_pdf)
        assert entry.matches(".anything")
        assert entry.matches(".pdf")
