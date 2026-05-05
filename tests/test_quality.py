from aseprite_mcp.tools.quality import _parse_layer_frame_ranges, _parse_overlap_pairs


class TestParseLayerFrameRanges:
    def test_empty(self):
        assert _parse_layer_frame_ranges(None) == "{}"

    def test_single_layer_single_range(self):
        result = _parse_layer_frame_ranges(["layer:1-10"])
        assert '"layer"' in result
        assert "{1,10}" in result

    def test_single_layer_multiple_ranges(self):
        result = _parse_layer_frame_ranges(["layer:1-5,10-15"])
        assert "{1,5}" in result
        assert "{10,15}" in result

    def test_multiple_layers(self):
        result = _parse_layer_frame_ranges(["bg:1-10", "fg:5-20"])
        assert '"bg"' in result
        assert '"fg"' in result

    def test_empty_input_list(self):
        assert _parse_layer_frame_ranges([]) == "{}"

    def test_skips_malformed_entries(self):
        result = _parse_layer_frame_ranges(["badentry"])
        assert result == "{}"

    def test_skips_entries_without_colon(self):
        result = _parse_layer_frame_ranges(["layer:1-10", "no_range"])
        assert '"layer"' in result

    def test_skips_invalid_numbers(self):
        result = _parse_layer_frame_ranges(["layer:abc-def"])
        assert result == "{}"


class TestParseOverlapPairs:
    def test_empty(self):
        assert _parse_overlap_pairs(None) == "{}"

    def test_single_pair_comma(self):
        result = _parse_overlap_pairs(["a,b"])
        assert '"a","b"' in result

    def test_single_pair_colon(self):
        result = _parse_overlap_pairs(["a:b"])
        assert '"a","b"' in result

    def test_multiple_pairs(self):
        result = _parse_overlap_pairs(["a,b", "c,d"])
        assert '"a","b"' in result
        assert '"c","d"' in result

    def test_skips_empty_entry(self):
        result = _parse_overlap_pairs([""])
        assert result == "{}"

    def test_skips_entry_without_separator(self):
        result = _parse_overlap_pairs(["justathing"])
        assert result == "{}"

    def test_empty_input_list(self):
        assert _parse_overlap_pairs([]) == "{}"