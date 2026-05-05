import pytest
from aseprite_mcp.core.commands import lua_escape, reject_traversal


class TestLuaEscape:
    def test_noop_on_simple_string(self):
        assert lua_escape("hello") == "hello"

    def test_escapes_backslash(self):
        assert lua_escape("a\\b") == "a\\\\b"

    def test_escapes_double_quote(self):
        assert lua_escape('say "hi"') == 'say \\"hi\\"'

    def test_escapes_newline(self):
        assert lua_escape("line1\nline2") == "line1\\nline2"

    def test_escapes_carriage_return(self):
        assert lua_escape("line1\rline2") == "line1\\rline2"

    def test_escapes_null(self):
        assert lua_escape("a\0b") == "a\\0b"

    def test_escapes_combined(self):
        result = lua_escape('path\\to\\"file"\nnew')
        assert "\\\\" in result
        assert '\\"' in result
        assert "\\n" in result

    def test_empty_string(self):
        assert lua_escape("") == ""


class TestRejectTraversal:
    def test_allows_simple_filename(self):
        assert reject_traversal("canvas.aseprite") is None

    def test_allows_nested_path(self):
        assert reject_traversal("subdir/canvas.aseprite") is None

    def test_allows_filename_with_dots(self):
        assert reject_traversal("my..file..name.aseprite") is None

    def test_rejects_parent_traversal(self):
        err = reject_traversal("../escape.aseprite")
        assert err is not None
        assert "traversal" in err.lower()

    def test_rejects_deep_traversal(self):
        err = reject_traversal("a/../../b/c.aseprite")
        assert err is not None

    def test_rejects_windows_traversal(self):
        err = reject_traversal("..\\escape.aseprite")
        assert err is not None

    def test_allows_absolute_path(self):
        assert reject_traversal("/safe/path/file.aseprite") is None

    def test_allows_windows_absolute(self):
        assert reject_traversal("C:/safe/path/file.aseprite") is None

    def test_rejects_traversal_deep_windows(self):
        err = reject_traversal("..\\..\\file.aseprite")
        assert err is not None