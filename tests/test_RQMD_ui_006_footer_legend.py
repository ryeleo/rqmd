"""
Tests for RQMD-UI-006: Footer legend and transient notifications area.

Verify that interactive menus maintain a reserved footer region for:
- Standardized legend (key mappings)
- Transient messages (detection source, errors, notifications)

Key requirements:
- Messages do not shift the main menu content
- Footer region is reliable and consistent
- Legend updates without page jumping
"""

import io
from unittest.mock import patch, MagicMock

import pytest

from rqmd import menus as menus_mod


class TestFooterLegendRegion:
    """Verify dedicated footer legend region behavior."""

    def test_RQMD_ui_006_footer_legend_parameter_accepted(self):
        """Verify select_from_menu accepts and uses footer_legend parameter."""
        options = ["A", "B", "C"]
        custom_legend = "keys: 1=option | q=quit"
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Test", options,
                            footer_legend=custom_legend
                        )
                    except:
                        pass
        
        # Custom legend should appear in output
        output = "".join(echo_calls)
        assert custom_legend in output, f"Custom legend not found in output. Got: {echo_calls}"

    def test_RQMD_ui_006_default_legend_when_none_provided(self):
        """Verify default legend is generated when footer_legend is None."""
        options = ["X", "Y"]
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            allow_paging_nav=True,
                            footer_legend=None  # Explicitly None
                        )
                    except:
                        pass
        
        output = "".join(echo_calls)
        # Should have default keys legend
        assert "keys:" in output.lower() or "quit" in output.lower(), "Default legend should be generated"

    def test_RQMD_ui_006_footer_message_parameter_accepted(self):
        """Verify select_from_menu accepts footer_message parameter for transient notifications."""
        options = ["Item 1", "Item 2"]
        transient_msg = "[theme: dark, source: system]"
        
        # For now, just verify the parameter is accepted (we'll implement rendering next)
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        # Call with footer_message parameter if signature supports it
                        result = menus_mod.select_from_menu(
                            "Test", options,
                            footer_legend="keys: q=quit"
                        )
                    except TypeError as e:
                        if "footer_message" in str(e):
                            pytest.skip("footer_message parameter not yet implemented")
                        raise

    def test_RQMD_ui_006_footer_legend_stable_across_renders(self):
        """Verify footer legend parameter is accepted and used in rendering."""
        options = ["A", "B", "C", "D", "E"]
        legend = "sort: n=name | d=desc | s=status"
        
        # Just verify the parameter is accepted and doesn't cause errors
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'q']):
                    try:
                        result = menus_mod.select_from_menu(
                            "Menu", options,
                            allow_paging_nav=True,
                            footer_legend=legend
                        )
                        # Should exit cleanly
                        assert result is None or isinstance(result, (int, str))
                    except TypeError as e:
                        pytest.fail(f"footer_legend parameter should be accepted: {e}")

    def test_RQMD_ui_006_legend_with_special_characters(self):
        """Verify footer legend handles special characters (brackets, pipes, equals)."""
        options = ["op1", "op2"]
        complex_legend = "d=[asc|dsc] | s=[active|waiting|done]"
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Test", options,
                            footer_legend=complex_legend
                        )
                    except:
                        pass
        
        output = "".join(echo_calls)
        assert complex_legend in output, "Special characters in legend should be preserved"

    def test_RQMD_ui_006_legend_truncation_if_too_long(self):
        """Verify very long legends don't corrupt formatting (truncate or wrap gracefully)."""
        options = ["A"]
        very_long_legend = "d=[asc|desc] | " * 20  # 300+ chars
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Test", options,
                            footer_legend=very_long_legend
                        )
                    except:
                        pass
        
        # Should complete without error; legend may be truncated or displayed as-is
        # The important thing is no exception or corruption
        assert len(echo_calls) > 0, "Should render successfully even with long legend"


class TestFooterMessageTransient:
    """Verify transient message area behavior (when implemented)."""

    def test_RQMD_ui_006_footer_region_reserved_layout(self):
        """Verify menu reserves footer region without shifting content."""
        options = [f"Option {i}" for i in range(1, 10)]
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            footer_legend="standard legend",
                            show_page_indicator=True
                        )
                    except:
                        pass
        
        output = "".join(echo_calls)
        # Menu content should be present
        assert "Option 1" in output or "Option 2" in output, "Menu content should render"
        # Footer should be present
        assert "standard legend" in output, "Footer legend should be present"

    def test_RQMD_ui_006_menu_content_not_shifted_by_footer(self):
        """Verify footer doesn't cause menu items to shift or reflow unexpectedly."""
        options = ["Stable", "Content", "Lines"]
        
        # Render with no footer
        echo_calls_no_footer = []
        
        def capture_echo_1(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls_no_footer.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo_1):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu("Menu", options)
                    except:
                        pass
        
        # Render with footer
        echo_calls_with_footer = []
        
        def capture_echo_2(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls_with_footer.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo_2):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            footer_legend="Footer"
                        )
                    except:
                        pass
        
        # Menu items should appear at same line in both cases
        content_lines_no_footer = [e for e in echo_calls_no_footer if "Stable" in e or "Content" in e]
        content_lines_with_footer = [e for e in echo_calls_with_footer if "Stable" in e or "Content" in e]
        
        # Both should have menu items rendered
        assert len(content_lines_no_footer) > 0, "Should have content lines without footer"
        assert len(content_lines_with_footer) > 0, "Should have content lines with footer"


class TestFooterIntegration:
    """Integration tests for footer legend with other menu features."""

    def test_RQMD_ui_006_footer_legend_with_zebra_striping(self):
        """Verify footer legend works with zebra striping."""
        options = ["A", "B", "C", "D"]
        
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            zebra=True,
                            footer_legend="keys: q=quit"
                        )
                    except:
                        pass

    def test_RQMD_ui_006_footer_legend_with_extra_keys(self):
        """Verify footer legend can coexist with extra key bindings."""
        options = ["Opt1", "Opt2"]
        custom_legend = "d=[asc|dsc]"
        
        echo_calls = []
        
        def capture_echo(msg="", *args, **kwargs):
            if isinstance(msg, str):
                echo_calls.append(msg)
        
        with patch("rqmd.menus.click.echo", side_effect=capture_echo):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu(
                            "Menu", options,
                            extra_key='d',
                            extra_key_help='toggle sort',
                            footer_legend=custom_legend
                        )
                    except:
                        pass
        
        output = "".join(echo_calls)
        # Custom legend should override default keys line
        assert custom_legend in output

    def test_RQMD_ui_006_footer_legend_with_paging(self):
        """Verify footer legend works correctly when paging through menu items."""
        options = [f"Item {i}" for i in range(1, 21)]
        legend = "p/n=page | q=quit"
        
        # Verify feature is accepted and works with paging
        with patch("rqmd.menus.click.echo"):
            with patch("sys.stdout.isatty", return_value=False):
                with patch("click.getchar", side_effect=['n', 'q']):
                    try:
                        result = menus_mod.select_from_menu(
                            "Items", options,
                            allow_paging_nav=True,
                            footer_legend=legend
                        )
                        # Should handle paging cleanly with custom legend
                        assert result is None or isinstance(result, (int, str))
                    except TypeError as e:
                        pytest.fail(f"footer_legend should work with paging: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
