import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.dirname(__file__))

class TestTUI(unittest.TestCase):
    @patch("curses.wrapper")
    def test_tui_initialization(self, mock_wrapper):
        from tui import UsageTUI
        tui = UsageTUI()
        self.assertIsInstance(tui, UsageTUI)
        
    @patch("token_usage.aggregate_usage")
    @patch("curses.newpad")
    @patch("curses.newwin")
    @patch("curses.curs_set")
    @patch("curses.doupdate")
    def test_tui_load_data(self, mock_doupdate, mock_curs_set, mock_newwin, mock_newpad, mock_aggregate):
        from tui import UsageTUI
        mock_aggregate.return_value = {"2026-02-05": {"model": {"input": 100, "cached": 0, "output": 0, "sessions": set(), "cost": 0.0}}}
        
        tui = UsageTUI()
        # Mock stdscr
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        # Mock getch to return 'q' immediately to exit the loop
        mock_stdscr.getch.return_value = ord('q')
        
        tui.main_loop(mock_stdscr)
        
        mock_aggregate.assert_called_once()
        mock_newpad.assert_called()

if __name__ == "__main__":
    unittest.main()
