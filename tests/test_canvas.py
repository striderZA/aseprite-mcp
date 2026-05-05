import pytest
from aseprite_mcp.tools.canvas import (
    create_canvas,
    add_layer,
    add_frame,
    set_frame,
    set_frame_duration,
    set_layer,
    delete_layer,
    set_layer_blend_mode,
    reorder_layer,
    flatten_layers,
    merge_down_layer,
    set_layer_label_color,
    set_cel_zindex,
)


class TestCanvasImports:
    def test_create_canvas_imported(self):
        assert callable(create_canvas)

    def test_add_layer_imported(self):
        assert callable(add_layer)

    def test_add_frame_imported(self):
        assert callable(add_frame)

    def test_set_frame_imported(self):
        assert callable(set_frame)

    def test_set_frame_duration_imported(self):
        assert callable(set_frame_duration)

    def test_set_layer_imported(self):
        assert callable(set_layer)

    def test_delete_layer_imported(self):
        assert callable(delete_layer)

    def test_set_layer_blend_mode_imported(self):
        assert callable(set_layer_blend_mode)

    def test_reorder_layer_imported(self):
        assert callable(reorder_layer)

    def test_flatten_layers_imported(self):
        assert callable(flatten_layers)

    def test_merge_down_layer_imported(self):
        assert callable(merge_down_layer)

    def test_set_layer_label_color_imported(self):
        assert callable(set_layer_label_color)

    def test_set_cel_zindex_imported(self):
        assert callable(set_cel_zindex)
