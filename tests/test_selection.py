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
