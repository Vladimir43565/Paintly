import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random

# --- CONFIGURATION ---
CURRENT_VERSION = "1.1.6" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Creative")
        self.root.geometry("1300x900")
        
        # Color Palette: Slate & Soft White
        self.clr_bg = "#f0f2f5"       # Light gray-blue background
        self.clr_side = "#ffffff"     # Pure white panels
        self.clr_accent = "#6366f1"   # Modern Indigo accent
        self.clr_text = "#1e293b"     # Slate text
        self.clr_border = "#e2e8f0"   # Soft border
        
        self.root.configure(bg=self.clr_bg)

        # Drawing State
        self.draw_color = "#1e293b"
        self.current_color = "#1e293b"
        self.brush_size = 5
        self.brush_type = "Ink" 
        self.stroke_history = [] 
        self.is_replaying = False
        
        self.setup_ui()

    def setup_ui(self):
        # 1. HEADER
        self.header = tk.Frame(self.root, bg=self.clr_side, height=60, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.header.pack(side="top", fill="x")

        title = tk.Label(self.header, text="Paintly", fg=self.clr_accent, bg=self.clr_side, font=("Segoe UI", 20, "bold"))
        title.pack(side="left", padx=25)

        self.update_btn = tk.Button(self.header, text="Check Updates", command=self.manual_update_check, 
                                   bg=self.clr_bg, fg=self.clr_text, relief="flat", padx=15, font=("Segoe UI", 9))
        self.update_btn.pack(side="right", padx=20, pady=12)

        # 2. FLOATING LEFT TOOLBAR
        self.toolbar_container = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=20)
        self.toolbar_container.pack(side="left", fill="y")

        self.tools = tk.Frame(self.toolbar_container, bg=self.clr_side, padx=10, pady=15, highlightthickness=1, highlightbackground=self.clr_border)
        self.tools.pack(fill="y")

        # Active Color Circle (Larger and centered)
        self.color_outer = tk.Frame(self.tools, bg=self.clr_border, width=48, height=48, pady=2, padx=2)
        self.color_outer.pack(pady=10)
        self.color_preview = tk.Frame(self.color_outer, bg=self.draw_color, width=44, height=44, cursor="hand2")
        self.color_preview.pack()
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        self.add_sep()

        # Brushes with modern styling
        brushes = [
            ("Pencil", "✏"), ("Soft", "🖌"), ("Ink", "🖋"), ("Spray", "✨"), ("Eraser", "🧽")
        ]
        for name, icon in brushes:
            btn = tk.Button(self.tools, text=f"{icon}  {name}", command=lambda n=name: self.set_brush(n),
                            bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 10), 
                            relief="flat", anchor="w", padx=10, pady=8, activebackground=self.clr_bg)
            btn.pack(fill="x")

        self.add_sep()

        # Replay Button
        tk.Button(self.tools, text="🎬 Watch Replay", command=self.run_replay, bg=self.clr_accent, 
                  fg="white", font=("Segoe UI", 10, "bold"), relief="flat", pady=8).pack(fill="x", pady=5)

        # Size Slider integrated into toolbar
        tk.Label(self.tools, text="Brush Size", bg=self.clr_side, fg="#64748b", font=("Segoe UI", 8)).pack(pady=(10,0))
        self.size_slider = tk.Scale(self.tools, from_=1, to=50, orient="horizontal", bg=self.clr_side, 
                                    highlightthickness=0, troughcolor=self.clr_bg, activebackground=self.clr_accent)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="x", pady=5)

        # 3. CANVAS AREA
        self.canvas_frame = tk.Frame(self.root, bg=self.clr_bg, padx=10, pady=10)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        
        # Shadow effect for canvas
        self.canvas_border = tk.Frame(self.canvas_frame, bg=self.clr_border, padx=1, pady=1)
        self.canvas_border.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_border, bg="#ffffff", highlightthickness=0, cursor="plus")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def add_sep(self):
        tk.Frame(self.tools, bg=self.clr_border, height=1).pack(fill="x", pady=15)

    def set_brush(self, b_name):
        if b_name == "Eraser":
            self.current_color = "#ffffff"
            self.brush_type = "Ink"
        else:
            self.current_color = self.draw_color
            self.brush_type = b_name

    def paint(self, event):
        if self.is_replaying: return
        self.brush_size = self.size_slider.get()
        x, y = event.x, event.y
        
        if self.brush_type == "Pencil":
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=1, fill="#94a3b8")
        elif self.brush_type == "Ink":
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=True)
        elif self.brush_type == "Soft":
            for i in range(2, 0, -1):
                self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size+(i*3), fill=self.current_color, capstyle=tk.ROUND)
        elif self.brush_type == "Spray":
            for _ in range(8):
                sx = x + random.randint(-self.brush_size*2, self.brush_size*2)
                sy = y + random.randint(-self.brush_size*2, self.brush_size*2)
                self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=self.current_color, outline="")

        self.stroke_history.append({'coords': (self.last_x, self.last_y, x, y), 'color': self.current_color, 'size': self.brush_size})
        self.last_x, self.last_y = x, y

    def start_draw(self, event): self.last_x, self.last_y = event.x, event.y
    def stop_draw(self, event): self.last_x, self.last_y = None, None

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def manual_update_check(self):
        try:
            r = requests.get(VERSION_URL, timeout=5)
            if r.status_code == 200 and r.text.strip() != CURRENT_VERSION:
                if messagebox.askyesno("Update", f"A new version ({r.text.strip()}) is available. Update?"):
                    self.do_update()
            else: messagebox.showinfo("Paintly", "You are on the latest version.")
        except: pass

    def do_update(self):
        try:
            new_code = requests.get(UPDATE_URL).text
            with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                f.write(new_code)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

    def run_replay(self):
        if not self.stroke_history or self.is_replaying: return
        self.is_replaying = True
        self.canvas.delete("all")
        def play(i):
            if i < len(self.stroke_history):
                s = self.stroke_history[i]
                self.canvas.create_line(s['coords'], fill=s['color'], width=s['size'], capstyle=tk.ROUND)
                self.root.after(3, lambda: play(i+1))
            else: self.is_replaying = False
        play(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
