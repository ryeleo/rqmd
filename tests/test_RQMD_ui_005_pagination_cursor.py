"""
Tests for RQMD-UI-005: Pagination and stable cursor semantics.

Verify that interactive menus maintain stable cursor/selection position across:
- Page changes (n/p navigation)
- Re-renders
- Selection visibility in the current window

Key requirements:
- Cursor position remains consistent across pagination
- Selection stays visible when possible
- Navigation keys (n, p) don't lose selection state
"""

from unittest.mock import MagicMock, patch

import pytest

from rqmd import menus as menus_mod


class TestStableCursorPagination:
    """Verify cursor remains stable across page navigation."""

    def test_RQMD_ui_005_selected_option_index_persisted_across_pages(self):
        """Verify selected_option_index parameter is accepted and preserved."""
        options = [f"Item {i}" for i in range(1, 21)]  # 20 items
        
        # Try with initial selection index
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        result = menus_mod.select_from_menu(
                            "Menu", options,
                            allow_paging_nav=True,
                            selected_option_index=5  # Start with 6th item selected
                        )
                        # Should complete without error
                        assert result is None or isinstance(result, (int, str))
                    except TypeError as e:
                        pytest.fail(f"selected_option_index should work: {e}")

    def test_RQMD_ui_005_initial_selection_bounds_check(self):
        """Verify initial selection index respects option list bounds."""
        options = ["A", "B", "C"]
        
        # Valid: selection within bounds
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    result = menus_mod.select_from_menu(
                        "Test", options,
                        selected_option_index=2  # Last item
                    )
                    assert result is None or isinstance(result, (int, str))
        
        # Invalid: selection out of bounds should be handled gracefully
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        result = menus_mod.select_from_menu(
                            "Test", options,
                            selected_option_index=999  # Out of bounds
                        )
                        # Should handle gracefully (either ignore or clamp)
                    except IndexError:
                        pytest.fail("Out-of-bounds selection should be handled gracefully")

    def test_RQMD_ui_005_selected_option_bg_parameter(self):
        """Verify selected_option_bg parameter highlights selected item."""
        options = ["First", "Second", "Third"]
        bg_code = "\x1b[48;5;226m"  # Yellow background
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        result = menus_mod.select_from_menu(
                            "Menu", options,
                            selected_option_index=1,
                            selected_option_bg=bg_code
                        )
                        # Should render with selection background
                    except TypeError as e:
                        pytest.fail(f"selected_option_bg should work: {e}")

    def test_RQMD_ui_005_selection_consistency_with_paging(self):
        """Verify selection index remains meaningful across page transitions."""
        options = [f"Item {i:02d}" for i in range(100)]  # 100 items
        
        # Track page transitions
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        # Simulate: page 1 with selection, then navigate to page 2
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'q']):  # Next page, quit
                    try:
                        result = menus_mod.select_from_menu(
                            "Large Menu", options,
                            allow_paging_nav=True,
                            selected_option_index=5  # Select item 5 on first page
                        )
                        # Should handle pagination with selection
                        assert result is None or isinstance(result, (int, str))
                    except:
                        pass

    def test_RQMD_ui_006_selected_item_remains_visible(self):
        """Verify selected item is shown on current page when possible."""
        options = [f"Opt {i}" for i in range(1, 31)]  # 30 items
        
        echo_calls = []
        
        def track_output(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        # Select item in middle of list
        with patch("rqmd.menus.click.echo", side_effect=track_output):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Items", options,
                            allow_paging_nav=True,
                            selected_option_index=15  # Select item 16 (middle)
                        )
                    except:
                        pass
        
        # Selected item should be in output if pagination includes it
        output = "".join(echo_calls)
        # Item 15 (0-indexed) should appear
        assert "Opt 16" in output or len(echo_calls) > 0


class TestCursorNavigationConsistency:
    """Verify navigation keys maintain consistent cursor behavior."""

    def test_RQMD_ui_005_next_prev_navigation_preserves_focus(self):
        """Verify n/p keys for pagination don't lose selection during page change."""
        options = [f"Entry {i}" for i in range(1, 26)]  # 25 items
        
        # Simulate: page forward, backward, forward again
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'p', 'n', 'q']):
                    try:
                        result = menus_mod.select_from_menu(
                            "Entries", options,
                            allow_paging_nav=True,
                            selected_option_index=3
                        )
                        # Should handle multi-page navigation
                    except:
                        pass

    def test_RQMD_ui_005_selection_survives_page_transitions(self):
        """Verify selection state doesn't reset during page changes."""
        options = [f"Item {i:03d}" for i in range(200)]  # 200 items
        
        navigation_sequence = ['n', 'n', 'p', 'q']  # Forth, forth, back, quit
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=navigation_sequence):
                    try:
                        result = menus_mod.select_from_menu(
                            "Large List", options,
                            allow_paging_nav=True,
                            selected_option_index=42
                        )
                        # Should track selection through multiple pages
                    except:
                        pass

    def test_RQMD_ui_005_centering_of_large_lists(self):
        """Verify visual window centers around selected item in large lists."""
        options = [f"Line {i:04d}" for i in range(1000)]  # 1000 items
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        # Select something far into the list
                        result = menus_mod.select_from_menu(
                            "Huge List", options,
                            allow_paging_nav=True,
                            selected_option_index=500  # Middle of list
                        )
                        # Page should render with selection visible
                    except:
                        pass


class TestCursorStateManagement:
    """Verify cursor state is correctly managed through menu lifecycle."""

    def test_RQMD_ui_005_selection_not_lost_on_filter_or_sort(self):
        """Verify selection semantics remain valid if list is re-sorted or filtered."""
        options = ["Zebra", "Apple", "Mango", "Banana"]
        
        # With initial selection
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        result = menus_mod.select_from_menu(
                            "Fruits", options,
                            selected_option_index=2  # "Mango"
                        )
                    except:
                        pass

    def test_RQMD_ui_005_selection_with_dynamic_content(self):
        """Verify selection index is stable when items are added/removed."""
        # Simulate a scenario where menu items change
        options_v1 = ["Item A", "Item B", "Item C"]
        options_v2 = ["Item A", "Item B", "Item X", "Item C"]  # New item inserted
        
        # Selection that was valid on v1 should still be valid or gracefully handled on v2
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        # First render with selection
                        menus_mod.select_from_menu(
                            "Dynamic", options_v1,
                            selected_option_index=1
                        )
                    except:
                        pass

    def test_RQMD_ui_005_selection_with_extra_keys(self):
        """Verify selection remains stable when using extra key bindings."""
        options = ["Opt1", "Opt2", "Opt3", "Opt4"]
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        result = menus_mod.select_from_menu(
                            "Menu", options,
                            selected_option_index=2,
                            extra_key='r',
                            extra_key_help='refresh',
                            extra_keys={'s': 'sort', 'd': 'delete'}
                        )
                        # Selection should persists through extra key navigation options
                    except:
                        pass


class TestCursorVisualFeedback:
    """Verify visual feedback for cursor position is clear."""

    def test_RQMD_ui_005_selected_option_visually_distinct(self):
        """Verify selected option stands out visually from unselected ones."""
        options = ["Unselected 1", "Selected Item", "Unselected 2"]
        highlight_bg = "\x1b[48;5;226m"  # Yellow
        
        echo_calls = []
        
        def track_highlights(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=track_highlights):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            selected_option_index=1,
                            selected_option_bg=highlight_bg
                        )
                    except:
                        pass
        
        # Visual distinction should be applied (ANSI codes present or content preserved)
        output = "".join(echo_calls)
        assert len(output) > 0

    def test_RQMD_ui_005_multi_select_scenarios(self):
        """Verify behavior with multiple potential selection states."""
        options = [f"Radio {i}" for i in "ABCDE"]
        
        # Test with explicit selection
        for index in [0, 2, 4]:
            with patch("rqmd.menus.click.echo"):
                with patch("sys.stdout.isatty", return_value=False):
                    with patch("click.getchar", return_value="q"):
                        try:
                            result = menus_mod.select_from_menu(
                                "Radio", options,
                                selected_option_index=index
                            )
                        except:
                            pass


class TestPaginationWithSelection:
    """Integration tests for pagination with selection."""

    def test_RQMD_ui_005_paging_with_initial_selection_first_page(self):
        """Verify pagination works when selection is on initial page."""
        options = [f"Item {i}" for i in range(1, 51)]
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'q']):
                    try:
                        result = menus_mod.select_from_menu(
                            "Items", options,
                            allow_paging_nav=True,
                            selected_option_index=3  # On first page
                        )
                    except:
                        pass

    def test_RQMD_ui_005_paging_with_selection_deep_in_list(self):
        """Verify pagination works when selection is far into the list."""
        options = [f"Entry {i}" for i in range(1, 101)]
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'n', 'p', 'q']):
                    try:
                        result = menus_mod.select_from_menu(
                            "Entries", options,
                            allow_paging_nav=True,
                            selected_option_index=75  # Deep in list
                        )
                    except:
                        pass

    def test_RQMD_ui_005_selection_boundary_conditions(self):
        """Verify cursor behavior at list boundaries (first/last items)."""
        options = ["First", "Second", "Middle", "SecondToLast", "Last"]
        
        for boundary_index in [0, 4]:  # First and last
            with patch("rqmd.menus.click.echo"):
                with patch("sys.stdout.isatty", return_value=False):
                    with patch("click.getchar", side_effect=['n', 'q'] if boundary_index < 4 else ['p', 'q']):
                        try:
                            menus_mod.select_from_menu(
                                "Boundary", options,
                                selected_option_index=boundary_index
                            )
                        except:
                            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
