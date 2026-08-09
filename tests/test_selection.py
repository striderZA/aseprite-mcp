"""Import verification for selection tools."""
from aseprite_mcp.tools.selection import (
    select_rectangle,
    select_all,
    deselect,
    get_selection,
    move_selection,
)


class TestSelectionToolImports:
    def test_select_rectangle_is_callable(self):
        assert callable(select_rectangle)

    def test_select_all_is_callable(self):
        assert callable(select_all)

    def test_deselect_is_callable(self):
        assert callable(deselect)

    def test_get_selection_is_callable(self):
        assert callable(get_selection)

    def test_move_selection_is_callable(self):
        assert callable(move_selection)


"""Region operation tools (selection.py)."""
from conftest import ok, run

from aseprite_mcp.tools import selection


def test_copy_region(sprite):
    ok(run(selection.copy_region(sprite, "body", 1, 8, 8, 8, 8, 20, 20)))


def test_move_region(sprite):
    ok(run(selection.move_region(sprite, "body", 1, 20, 20, 8, 8, 0, 0)))


def test_erase_region(sprite):
    ok(run(selection.erase_region(sprite, "body", 1, 0, 0, 4, 4)))


def test_erase_color(sprite):
    result = ok(run(selection.erase_color(sprite, "body", 1, "#D04648", 0)))
    assert "Erased" in result
