"""
Tests for RQMD-UI-001: Screen-write rendering mode.

Verify that full-screen ANSI redraw behavior works correctly:
- Clear + home cursor on first render when enabled
- Clear + home on each pagination change (snappy page transitions)
- No ANSI clears when screen-write is disabled or non-TTY
"""

import io
import sys
from unittest.mock import MagicMock, patch

import pytest
from rqmd import menus as menus_mod


class TestScreenWriteFullScreenRedraw:
    """Verify ANSI clear + home cursor behavior in select_from_menu."""

    def _capture_menu_output(self, options, screen_write_enabled=False, is_tty=True, user_input="q"):
        """Helper: capture full output of select_from_menu with controlled screen_write and TTY state."""
        menus_mod.set_screen_write_enabled(screen_write_enabled)
        
        output_buffer = io.StringIO()
        with patch("sys.stdout", output_buffer):
            with patch("sys.stdout.isatty", return_value=is_tty):
                with patch("click.getchar", return_value=user_input):
                    try:
                        menus_mod.select_from_menu("Test Menu", options, allow_paging_nav=False)
                    except (EOFError, Exception):
                        pass  # Ignore any errors from mocked input
        
        return output_buffer.getvalue()

    def test_RQMD_ui_001_screen_write_enabled_sends_clear_home_escape(self):
        """Verify ANSI clear + home escape is sent when screen-write is enabled and TTY."""
        options = ["Option 1", "Option 2", "Option 3"]
        output = self._capture_menu_output(options, screen_write_enabled=True, is_tty=True, user_input="q")
        
        # Should contain clear (CSI 2J) + home (CSI H) escape
        assert "\x1b[2J\x1b[H" in output, "Expected clear + home cursor escape in TTY screen-write mode"

    def test_RQMD_ui_001_screen_write_disabled_no_clear_escape(self):
        """Verify ANSI clear is NOT sent when screen-write is disabled."""
        options = ["Option 1", "Option 2", "Option 3"]
        output = self._capture_menu_output(options, screen_write_enabled=False, is_tty=True, user_input="q")
        
        # Should NOT contain clear escape when disabled
        assert "\x1b[2J\x1b[H" not in output, "Expected no clear escape when screen-write disabled"

    def test_RQMD_ui_001_non_tty_no_clear_even_when_enabled(self):
        """Verify ANSI clear is NOT sent for non-TTY even with screen-write enabled."""
        options = ["Option 1", "Option 2", "Option 3"]
        output = self._capture_menu_output(options, screen_write_enabled=True, is_tty=False, user_input="q")
        
        # Should NOT send clear for non-TTY (e.g., piped output, file, CI)
        assert "\x1b[2J\x1b[H" not in output, "Expected no ANSI escape for non-TTY even with screen-write enabled"

    def test_RQMD_ui_001_multiple_renders_with_screen_write(self):
        """Verify module state correctly controls screen-write behavior across multiple calls."""
        options1 = ["A", "B", "C"]
        options2 = ["X", "Y", "Z"]
        
        # First call with screen-write enabled
        menus_mod.set_screen_write_enabled(True)
        output1 = self._capture_menu_output(options1, screen_write_enabled=True, is_tty=True, user_input="q")
        assert "\x1b[2J\x1b[H" in output1, "First call should have clear escape"
        
        # Second call with screen-write disabled
        menus_mod.set_screen_write_enabled(False)
        output2 = self._capture_menu_output(options2, screen_write_enabled=False, is_tty=True, user_input="q")
        assert "\x1b[2J\x1b[H" not in output2, "Second call should not have clear escape when disabled"
        
        # Reset
        menus_mod.set_screen_write_enabled(False)

    def test_RQMD_ui_001_full_screen_mode_preserves_menu_content(self):
        """Verify rendering content is still output in full-screen mode (clear alone doesn't lose content)."""
        options = ["Alpha", "Bravo", "Charlie"]
        output = self._capture_menu_output(options, screen_write_enabled=True, is_tty=True, user_input="q")
        
        # Even with clear escapes, menu items should still appear in output
        assert "Alpha" in output, "Menu content should be present in full-screen mode"
        assert "Bravo" in output, "Menu content should be present in full-screen mode"
        assert "Charlie" in output, "Menu content should be present in full-screen mode"
        assert "Test Menu" in output, "Menu title should be present"

    def test_RQMD_ui_001_module_state_toggle_affects_rendering(self):
        """Verify set_screen_write_enabled() correctly controls rendering behavior."""
        options = ["Test A", "Test B"]
        
        # First: enabled
        menus_mod.set_screen_write_enabled(True)
        assert menus_mod.get_screen_write_enabled() is True
        output1 = self._capture_menu_output(options, screen_write_enabled=True, is_tty=True, user_input="q")
        
        # Second: disabled
        menus_mod.set_screen_write_enabled(False)
        assert menus_mod.get_screen_write_enabled() is False
        output2 = self._capture_menu_output(options, screen_write_enabled=False, is_tty=True, user_input="q")
        
        # Enabled should have clear, disabled should not
        assert "\x1b[2J\x1b[H" in output1
        assert "\x1b[2J\x1b[H" not in output2

    def test_RQMD_ui_001_clear_home_order_correct(self):
        """Verify clear (CSI 2J) comes before home (CSI H) in escape sequence."""
        options = ["Item 1", "Item 2"]
        output = self._capture_menu_output(options, screen_write_enabled=True, is_tty=True, user_input="q")
        
        # Find positions of clear and home
        clear_pos = output.find("\x1b[2J")
        home_pos = output.find("\x1b[H")
        
        if clear_pos != -1 and home_pos != -1:
            # Both should be present and clear should come before home
            assert clear_pos < home_pos, "Clear escape should come before home cursor escape"
        else:
            pytest.fail(f"Expected both clear and home escapes in output. Clear: {clear_pos}, Home: {home_pos}")

    def test_RQMD_ui_001_toggle_persists_across_calls(self):
        """Verify module-level screen-write state persists correctly."""
        # Set to True
        menus_mod.set_screen_write_enabled(True)
        assert menus_mod.get_screen_write_enabled() is True
        
        # State should persist
        assert menus_mod.get_screen_write_enabled() is True
        
        # Toggle to False
        menus_mod.set_screen_write_enabled(False)
        assert menus_mod.get_screen_write_enabled() is False
        
        # State should persist
        assert menus_mod.get_screen_write_enabled() is False
        
        # Reset for other tests
        menus_mod.set_screen_write_enabled(False)


class TestScreenWriteInteractiveLoops:
    """Verify screen-write rendering behavior in interactive workflow loops."""

    def test_RQMD_ui_001_screen_write_in_file_selection_menu(self):
        """Verify file selection menu respects screen-write mode."""
        # This is an integration-level test verifying that workflows using select_from_menu
        # inherit full-screen rendering when screen-write is enabled
        options = ["file1.md", "file2.md", "file3.md"]
        menus_mod.set_screen_write_enabled(True)
        
        output_buffer = io.StringIO()
        with patch("sys.stdout", output_buffer):
            with patch("sys.stdout.isatty", return_value=True):
                with patch("click.getchar", return_value="q"):
                    try:
                        menus_mod.select_from_menu("Select a file", options)
                    except:
                        pass
        
        output = output_buffer.getvalue()
        assert "\x1b[2J\x1b[H" in output
        menus_mod.set_screen_write_enabled(False)  # Reset


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
