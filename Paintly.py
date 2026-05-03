import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random

# --- CONFIGURATION ---
CURRENT_VERSION = "1.1.9" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Creative")
        self.root.geometry("1300x900")
        
        # Theme States
        self.dark_mode = False
        self.set_theme_colors()
        
        # Drawing State
        self.draw_color = "#1e293b"
        self.current_color = "#1e293b"
        self.brush_size = 5
        self.brush_type = "Ink" 
        self.stroke_history = [] 
        self.is_replaying = False
        
        self.replay_speed_var = tk.DoubleVar(value=1.0)
        
        self.setup_ui()

    def set_theme_colors(self):
        if self.dark_mode:
            self.clr_bg = "#121212"
            self.clr_side = "#1e1e1e"
            self.clr_accent = "#818cf8"
            self.clr_text = "#f8fafc"
            self.clr_border = "#334155"
            self.canvas_bg = "#1e1e1e"
        else:
            self.clr_bg = "#f0f2f5"
            self.clr_side = "#ffffff"
            self.clr_accent = "#6366f1"
            self.clr_text = "#1e293b"
            self.clr_border = "#e2e8f0"
            self.canvas_bg = "#ffffff"

    def setup_ui(self):
        # Clear existing UI for theme switching
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.configure(bg=self.clr_bg)

        # 1. HEADER
        self.header = tk.Frame(self.root, bg=self.clr_side, height=60, highlightthickness=1, highlightbackground=self.clr_border)
        self.header.pack(side="top", fill="x")

        title = tk.Label(self.header, text="Paintly", fg=self.clr_accent, bg=self.clr_side, font=("Segoe UI", 20, "bold"))
        title.pack(side="left", padx=25)

        self.update_btn = tk.Button(self.header, text="Check Updates", command=self.manual_update_check, 
                                   bg=self.clr_bg, fg=self.clr_text, relief="flat", padx=15, font=("Segoe UI", 9))
        self.update_btn.pack(side="right", padx=20, pady=12)

        # 2. TOOLBAR
        self.toolbar_container = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=20)
        self.toolbar_container.pack(side="left", fill="y")

        self.tools = tk.Frame(self.toolbar_container, bg=self.clr_side, padx=10, pady=15, highlightthickness=1, highlightbackground=self.clr_border)
        self.tools.pack(fill="y")

        # Color Preview
        self.color_preview = tk.Frame(self.tools, bg=self.draw_color, width=44, height=44, cursor="hand2", highlightthickness=1, highlightbackground=self.clr_border)
        self.color_preview.pack(pady=10)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        self.add_sep()

        # Brushes
        brushes = [("Pencil", "✏"), ("Soft", "🖌"), ("Ink", "🖋"), ("Spray", "✨"), ("Eraser", "🧽")]
        for name, icon in brushes:
            btn = tk.Button(self.tools, text=f"{icon}  {name}", command=lambda n=name: self.set_brush(n),
                            bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 10), 
                            relief="flat", anchor="w", padx=10, pady=6, activebackground=self.clr_bg)
            btn.pack(fill="x")

        self.add_sep()

        # REPLAY SPEED (Fixed for Super Fast 5x)
        tk.Label(self.tools, text="REPLAY SPEED", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8, "bold")).pack(pady=(0,5))
        speed_frame = tk.Frame(self.tools, bg=self.clr_side)
        speed_frame.pack(fill="x")
        
        for spd in [1, 2, 5]:
            tk.Radiobutton(speed_frame, text=f"{spd}x", variable=self.replay_speed_var, value=spd,
                           bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8),
                           indicatoron=0, selectcolor=self.clr_accent, relief="flat", padx=5).pack(side="left", expand=True)

        tk.Button(self.tools, text="🎬 Watch Replay", command=self.run_replay, bg=self.clr_accent, 
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat", pady=8).pack(fill="x", pady=(10,5))

        self.add_sep()

        # SETTINGS (Theme Toggle)
        tk.Label(self.tools, text="SETTINGS", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8, "bold")).pack()
        theme_text = "🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode"
        tk.Button(self.tools, text=theme_text, command=self.toggle_theme, bg=self.clr_bg, 
                  fg=self.clr_text, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=5)

        # 3. CANVAS
        self.canvas_frame = tk.Frame(self.root, bg=self.clr_bg, padx=10, pady=10)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.canvas_bg, highlightthickness=1, highlightbackground=self.clr_border, cursor="plus")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.set_theme_colors()
        self.setup_ui()

    def add_sep(self):
        tk.Frame(self.tools, bg=self.clr_border, height=1).pack(fill="x", pady=15)

    def set_brush(self, b_name):
        if b_name == "Eraser":
            self.current_color = self.canvas_bg
            self.brush_type = "Ink"
        else:
            self.current_color = self.draw_color
            self.brush_type = b_name

    def paint(self, event):
        if self.is_replaying: return
        x, y = event.x, event.y
        if self.brush_type == "Pencil":
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=1, fill=self.clr_text)
        else:
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=True)

        self.stroke_history.append({'coords': (self.last_x, self.last_y, x, y), 'color': self.current_color, 'size': self.brush_size})
        self.last_x, self.last_y = x, y

    def start_draw(self, event): self.last_x, self.last_y = event.x, event.y
    def stop_draw(self, event): self.last_x, self.last_y = None, None

    def run_replay(self):
        if not self.stroke_history or self.is_replaying: return
        self.is_replaying = True
        self.canvas.delete("all")
        
        multiplier = self.replay_speed_var.get()
        # 5x is now optimized to 1ms delay or even processing multiple strokes per tick
        delay = max(1, int(10 / multiplier))
        strokes_per_tick = 1 if multiplier < 5 else 3 # Batch strokes at 5x for "super fast" feel

        def play(i):
            if i < len(self.stroke_history):
                for _ in range(strokes_per_tick):
                    if i < len(self.stroke_history):
                        s = self.stroke_history[i]
                        self.canvas.create_line(s['coords'], fill=s['color'], width=s['size'], capstyle=tk.ROUND)
                        i += 1
                self.root.after(delay, lambda: play(i))
            else: self.is_replaying = False
        play(0)

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def manual_update_check(self):
        try:
            cache_buster = f"?t={random.randint(1, 999999)}"
            r = requests.get(VERSION_URL + cache_buster, timeout=5)
            if r.status_code == 200:
                remote_v = r.text.strip()
                remote_parts = [int(p) for p in remote_v.split('.')]
                local_parts = [int(p) for p in CURRENT_VERSION.split('.')]
                if remote_parts > local_parts:
                    if messagebox.askyesno("Update", f"New version {remote_v} available. Update?"):
                        self.do_update()
                else: messagebox.showinfo("Paintly", f"Up to date! (v{CURRENT_VERSION})")
        except: pass

    def do_update(self):
        try:
            new_code = requests.get(UPDATE_URL + f"?t={random.randint(1,999)}").text
            with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                f.write(new_code)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
