#!/usr/bin/env python3
import curses
import token_usage
import json
from datetime import datetime

class UsageTUI:
    def __init__(self):
        self.stats = {}
        self.current_filter = "all"
        self.show_models = False
        self.running = True
        self.scroll_y = 0
        self.selected_row = 0
        self.view_rows = [] # List of lists [col1, col2, ...]
        self.view_data = [] # List of (display_text, raw_key)
        self.col_widths = []
        self.totals = {"input": 0, "cached": 0, "output": 0, "cost": 0.0}
        self.model_totals = {}
        self.filter_options = ["all", "today", "yesterday", "this-week", "last-week", "this-month", "last-month"]
        self.show_filter_menu = False
        self.menu_selected = 0
        self.table_pad = None

    def load_data(self):
        self.stats = token_usage.aggregate_usage()
        self.refresh_view_data()

    def refresh_view_data(self):
        self.view_rows = []
        self.view_data = []
        self.totals = {"input": 0, "cached": 0, "output": 0, "cost": 0.0}
        self.model_totals = {}
        
        filtered_stats = self.stats
        if self.current_filter != "all":
            start_date, end_date = token_usage.get_date_range(self.current_filter)
            if start_date and end_date:
                filtered_stats = token_usage.filter_stats(self.stats, start_date, end_date)
        
        # 1. Aggregate totals and model totals
        for date in sorted(filtered_stats.keys(), reverse=True):
            if date == "unknown": continue
            for model, s in filtered_stats[date].items():
                if model not in self.model_totals:
                    self.model_totals[model] = {"input": 0, "cached": 0, "output": 0, "cost": 0.0}
                self.model_totals[model]["input"] += s["input"]
                self.model_totals[model]["cached"] += s["cached"]
                self.model_totals[model]["output"] += s["output"]
                self.model_totals[model]["cost"] += s["cost"]
                self.totals["input"] += s["input"]
                self.totals["cached"] += s["cached"]
                self.totals["output"] += s["output"]
                self.totals["cost"] += s["cost"]

        # 2. Build raw rows
        for date in sorted(filtered_stats.keys(), reverse=True):
            if date == "unknown": continue
            if not self.show_models:
                day_input = sum(s["input"] for s in filtered_stats[date].values())
                day_cached = sum(s["cached"] for s in filtered_stats[date].values())
                day_output = sum(s["output"] for s in filtered_stats[date].values())
                day_sessions = set()
                for s in filtered_stats[date].values(): day_sessions.update(s["sessions"])
                day_cost = sum(s["cost"] for s in filtered_stats[date].values())
                total = day_input + day_cached + day_output
                self.view_rows.append([
                    date, str(len(day_sessions)), f"{day_input:,}", f"{day_cached:,}", 
                    f"{day_output:,}", f"{total:,}", f"${day_cost:,.2f}"
                ])
            else:
                for model in sorted(filtered_stats[date].keys()):
                    s = filtered_stats[date][model]
                    total = s["input"] + s["cached"] + s["output"]
                    self.view_rows.append([
                        date, model, str(len(s['sessions'])), f"{s['input']:,}", 
                        f"{s['cached']:,}", f"{s['output']:,}", f"{total:,}", f"${s['cost']:,.2f}"
                    ])

        # 3. Add totals to row width calculation context
        totals_context = []
        if self.show_models:
            for model in sorted(self.model_totals.keys()):
                m = self.model_totals[model]
                totals_context.append(["", f"TOTAL ({model})", "", f"{m['input']:,}", f"{m['cached']:,}", f"{m['output']:,}", f"{m['input']+m['cached']+m['output']:,}", f"${m['cost']:,.2f}"])
        
        grand_total_row = ["", "GRAND TOTAL (ALL)", "", f"{self.totals['input']:,}", f"{self.totals['cached']:,}", f"{self.totals['output']:,}", f"{self.totals['input']+self.totals['cached']+self.totals['output']:,}", f"${self.totals['cost']:,.2f}"]
        if not self.show_models:
            grand_total_row = ["", "", f"{self.totals['input']:,}", f"{self.totals['cached']:,}", f"{self.totals['output']:,}", f"{self.totals['input']+self.totals['cached']+self.totals['output']:,}", f"${self.totals['cost']:,.2f}"]

        # 4. Calculate column widths
        header = ["DATE", "MODEL", "SESS", "INPUT", "CACHED", "OUTPUT", "TOTAL", "COST"] if self.show_models else ["DATE", "SESS", "INPUT", "CACHED", "OUTPUT", "TOTAL", "COST"]
        all_potential_rows = [header] + self.view_rows + totals_context + [grand_total_row]
        num_cols = len(header)
        self.col_widths = [0] * num_cols
        for row in all_potential_rows:
            for i in range(min(len(row), num_cols)):
                self.col_widths[i] = max(self.col_widths[i], len(str(row[i])))

        # 5. Generate display data
        for row in self.view_rows:
            line = ""
            for i, val in enumerate(row):
                align = "<" if i < (2 if self.show_models else 1) else ">"
                line += f"{val:{align}{self.col_widths[i]}}  "
            self.view_data.append((line.rstrip(), row[0]))

    def draw_header(self, stdscr):
        h, w = stdscr.getmaxyx()
        model_status = "ON" if self.show_models else "OFF"
        header = f" Gemini Token Usage TUI | Filter: [{self.current_filter}] | Models: {model_status} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        stdscr.attron(curses.A_REVERSE)
        try:
            stdscr.addstr(0, 0, header.ljust(w)[:w-1])
        except curses.error:
            pass
        stdscr.attroff(curses.A_REVERSE)

    def draw_totals(self, stdscr, start_row, height):
        h, w = stdscr.getmaxyx()
        if height <= 2: height = 3
        
        win = curses.newwin(height, w, start_row, 0)
        win.box()
        win.attron(curses.A_BOLD)
        win.addstr(0, 2, f" TOTALS ({self.current_filter}) ")
        win.attroff(curses.A_BOLD)
        
        row_idx = 1
        label_col_width = self.col_widths[0] + 2 + self.col_widths[1] if self.show_models else self.col_widths[0]
        
        def format_total_line(label, stats_dict):
            parts = [f"{label:<{label_col_width}}"]
            if self.show_models: parts.append(f"{'':>{self.col_widths[2]}}") 
            parts.append(f"{stats_dict['input']:>{self.col_widths[-5]},}")
            parts.append(f"{stats_dict['cached']:>{self.col_widths[-4]},}")
            parts.append(f"{stats_dict['output']:>{self.col_widths[-3]},}")
            parts.append(f"{(stats_dict['input']+stats_dict['cached']+stats_dict['output']):>{self.col_widths[-2]},}")
            
            cost_str = f"${stats_dict['cost']:,.2f}"
            parts.append(f"{cost_str:>{self.col_widths[-1]}}")
            return "  ".join(parts)

        if self.show_models:
            sorted_models = sorted(self.model_totals.keys())
            for model in sorted_models:
                if row_idx >= height - 2: break
                line = format_total_line(f"TOTAL ({model[:30]})", self.model_totals[model])
                win.addstr(row_idx, 1, line[:w-2])
                row_idx += 1
            if row_idx < height - 1:
                win.addstr(row_idx, 1, ("-" * (w - 2))[:w-2])
                row_idx += 1

        if row_idx < height - 1:
            line = format_total_line("GRAND TOTAL (ALL)", self.totals)
            win.attron(curses.A_BOLD)
            win.addstr(row_idx, 1, line[:w-2])
            win.attroff(curses.A_BOLD)
        
        win.refresh()

    def draw_filter_menu(self, stdscr):
        h, w = stdscr.getmaxyx()
        menu_h = len(self.filter_options) + 2
        menu_w = 20
        start_y = (h - menu_h) // 2
        start_x = (w - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, start_y, start_x)
        win.box()
        win.addstr(0, 2, " Select Filter ")
        for i, option in enumerate(self.filter_options):
            if i == self.menu_selected: win.attron(curses.A_REVERSE)
            win.addstr(i + 1, 2, option.center(menu_w - 4))
            if i == self.menu_selected: win.attroff(curses.A_REVERSE)
        win.refresh()

    def draw_footer(self, stdscr):
        h, w = stdscr.getmaxyx()
        footer = " [Q] Quit | [R] Refresh | [M] Models | [F] Filter | [P] Pricing | [UP/DOWN] Select "
        stdscr.attron(curses.A_REVERSE)
        try:
            stdscr.addstr(h - 1, 0, footer.ljust(w)[:w-1])
        except curses.error:
            pass
        stdscr.attroff(curses.A_REVERSE)

    def edit_pricing(self, stdscr):
        import os, subprocess
        from pathlib import Path
        pricing_path = Path.home() / ".gemini" / "pricing.json"
        pricing_path.parent.mkdir(parents=True, exist_ok=True)
        if not pricing_path.exists():
            with pricing_path.open("w") as f: json.dump({"flash_patterns": [], "pro_patterns": []}, f, indent=2)
        curses.def_shell_mode()
        stdscr.clear(); stdscr.refresh()
        subprocess.call([os.environ.get('EDITOR', 'vi'), str(pricing_path)])
        curses.reset_shell_mode()
        token_usage.reload_config(); self.load_data(); self.table_pad = None

    def main_loop(self, stdscr):
        curses.curs_set(0); stdscr.keypad(True); stdscr.nodelay(False)
        self.load_data(); self.table_pad = None
        while self.running:
            stdscr.erase(); self.draw_header(stdscr); self.draw_footer(stdscr)
            h, w = stdscr.getmaxyx()
            totals_h = 3
            if self.show_models: totals_h = min(len(self.model_totals) + 4, h // 3)
            table_y_start = 2; table_y_end = h - totals_h - 2; table_h = table_y_end - table_y_start + 1
            header_cols = ["DATE", "MODEL", "SESS", "INPUT", "CACHED", "OUTPUT", "TOTAL", "COST"] if self.show_models else ["DATE", "SESS", "INPUT", "CACHED", "OUTPUT", "TOTAL", "COST"]
            col_header = ""
            for i, col in enumerate(header_cols):
                align = "<" if i < (2 if self.show_models else 1) else ">"
                col_header += f"{col:{align}{self.col_widths[i]}}  "
            try: stdscr.addstr(1, 0, col_header[:w-1])
            except curses.error: pass
            if not self.table_pad:
                self.table_pad = curses.newpad(max(len(self.view_data) + 1, 100), 200)
            self.table_pad.erase()
            for i, (line, _) in enumerate(self.view_data):
                if i == self.selected_row: self.table_pad.attron(curses.A_REVERSE)
                self.table_pad.addstr(i, 0, line)
                if i == self.selected_row: self.table_pad.attroff(curses.A_REVERSE)
            if self.selected_row < self.scroll_y: self.scroll_y = self.selected_row
            elif self.selected_row >= self.scroll_y + table_h: self.scroll_y = self.selected_row - table_h + 1
            stdscr.noutrefresh()
            if table_h > 0: self.table_pad.noutrefresh(self.scroll_y, 0, table_y_start, 0, table_y_end, w - 1)
            self.draw_totals(stdscr, h - totals_h - 1, totals_h)
            if self.show_filter_menu: self.draw_filter_menu(stdscr)
            curses.doupdate()
            key = stdscr.getch()
            if self.show_filter_menu:
                if key == curses.KEY_UP: self.menu_selected = (self.menu_selected - 1) % len(self.filter_options)
                elif key == curses.KEY_DOWN: self.menu_selected = (self.menu_selected + 1) % len(self.filter_options)
                elif key in [10, 13, curses.KEY_ENTER]:
                    self.current_filter = self.filter_options[self.menu_selected]
                    self.show_filter_menu = False; self.selected_row = 0; self.scroll_y = 0; self.refresh_view_data(); self.table_pad = None
                elif key in [27, ord('f'), ord('F')]: self.show_filter_menu = False
                continue
            if key in [ord('q'), ord('Q')]: self.running = False
            elif key in [ord('r'), ord('R')]: self.load_data(); self.table_pad = None
            elif key in [ord('p'), ord('P')]: self.edit_pricing(stdscr)
            elif key in [ord('f'), ord('F')]: self.show_filter_menu = True; self.menu_selected = self.filter_options.index(self.current_filter)
            elif key in [ord('m'), ord('M')]:
                self.show_models = not self.show_models; self.selected_row = 0; self.scroll_y = 0; self.refresh_view_data(); self.table_pad = None
            elif key == curses.KEY_UP: self.selected_row = max(0, self.selected_row - 1)
            elif key == curses.KEY_DOWN: self.selected_row = min(len(self.view_data) - 1, self.selected_row + 1)
            elif key == curses.KEY_PPAGE: self.selected_row = max(0, self.selected_row - 10)
            elif key == curses.KEY_NPAGE: self.selected_row = min(len(self.view_data) - 1, self.selected_row + 10)

def main():
    tui = UsageTUI(); curses.wrapper(tui.main_loop)
if __name__ == "__main__":
    main()
