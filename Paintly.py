import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math

# --- CONFIGURATION ---
CURRENT_VERSION = "1.1.4" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Pro — {CURRENT_VERSION}")
        self.root.geometry("1250x850")
        
        # Theme Colors (Modern Dark)
        self.bg_main = "#1a1a1a"
        self.bg_panel = "#252526"
        self.accent = "#007acc"
        self.text_color = "#cccccc"
        
        self.root.configure(bg=self.bg_main)

        # Drawing State
        self.draw_color = "#ffffff"
        self.current_color = "#ffffff"
        self.brush_size = 5
        self.brush_type = "Ink" 
        self.stroke_history = [] 
        self.is_replaying = False
        
        self.setup_ui()

    def setup_ui(self):
        # 1. TOP BAR (Clean & Modern)
        self.top_bar = tk.Frame(self.root, bg=self.bg_panel, height=50, pady=5)
        self.top_bar.pack(side="top", fill="x")

        title_label = tk.Label(self.top_bar, text="PAINTLY PRO", fg=self.accent, bg=self.bg_panel, font=("Impact", 18))
        title_label.pack(side="left", padx=20)

        # Update Button moved to top right
        self.update_btn = tk.Button(self.top_bar, text="Check for Update", command=self.manual_update_check, 
                                   bg=self.bg_main, fg=self.text_color, relief="flat", padx=10)
        self.update_btn.pack(side="right", padx=10)

        # 2. LEFT FLOATING-STYLE PANEL
        self.tool_panel = tk.Frame(self.root, bg=self.bg_panel, width=70, padx=10, pady=20)
        self.tool_panel.pack(side="left", fill="y", padx=10, pady=10)

        # Color Circle
        self.color_preview = tk.Frame(self.tool_panel, bg=self.draw_color, width=40, height=40, cursor="hand2")
        self.color_preview.pack(pady=10)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        self.add_tool_sep()

        # BRUSH TYPES (New System)
        brushes = [
            ("✏️", "Pencil"),
            ("🖌️", "Soft"),
            ("🖋️", "Ink"),
            ("🌈", "Gradient"),
            ("💥", "Spray")
        ]
        for icon, b_type in brushes:
            btn = tk.Button(self.tool_panel, text=icon, command=lambda t=b_type: self.set_brush_type(t),
                            bg=self.bg_panel, fg="white", font=("Arial", 14), relief="flat", activebackground=self.accent)
            btn.pack(fill="x", pady=5)

        self.add_tool_sep()

        # Replay
        tk.Button(self.tool_panel, text="▶", command=self.run_replay, bg=self.bg_panel, fg="#f1c40f", 
                  font=("Arial", 14), relief="flat").pack(fill="x", pady=5)

        # 3. CANVAS (Rounded Container)
        self.canvas_container = tk.Frame(self.root, bg=self.bg_main, padx=10, pady=10)
        self.canvas_container.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="#ffffff", highlightthickness=0, cursor="pencil")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # 4. BOTTOM STATUS BAR
        self.status_bar = tk.Frame(self.root, bg=self.accent, height=25)
        self.status_bar.pack(side="bottom", fill="x")
        self.status_label = tk.Label(self.status_bar, text=f"Brush: {self.brush_type} | Size: {self.brush_size}", 
                                    fg="white", bg=self.accent, font=("Arial", 9))
        self.status_label.pack(side="left", padx=10)

    def add_tool_sep(self):
        tk.Frame(self.tool_panel, bg="#444444", height=2).pack(fill="x", pady=10)

    def set_brush_type(self, b_type):
        self.brush_type = b_type
        self.status_label.config(text=f"Brush: {self.brush_type} | Size: {self.brush_size}")

    def paint(self, event):
        if self.is_replaying: return
        x, y = event.x, event.y
        
        if self.brush_type == "Pencil":
            # Thin, slightly transparent look
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=1, fill="#555555", capstyle=tk.BUTT)
        
        elif self.brush_type == "Ink":
            # Sharp, bold
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND)

        elif self.brush_type == "Soft":
            # Mimic soft edges by drawing multiple lines with decreasing width
            for i in range(3, 0, -1):
                alpha_w = self.brush_size + (i * 2)
                self.canvas.create_line(self.last_x, self.last_y, x, y, width=alpha_w, fill=self.current_color, capstyle=tk.ROUND)

        elif self.brush_type == "Spray":
            for _ in range(10):
                sx = x + random.randint(-self.brush_size*2, self.brush_size*2)
                sy = y + random.randint(-self.brush_size*2, self.brush_size*2)
                self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=self.current_color, outline=self.current_color)

        elif self.brush_type == "Gradient":
            # Shifts color slightly as you move
            r, g, b = self.root.winfo_rgb(self.current_color)
            r = (r // 256 + random.randint(-10, 10)) % 255
            new_col = f'#{r:02x}{g // 256:02x}{b // 256:02x}'
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=new_col)

        self.stroke_history.append({'coords': (self.last_x, self.last_y, x, y), 'color': self.current_color, 'size': self.brush_size, 'type': self.brush_type})
        self.last_x, self.last_y = x, y

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def stop_draw(self, event):
        self.last_x, self.last_y = None, None

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def manual_update_check(self):
        try:
            r = requests.get(VERSION_URL, timeout=5)
            if r.status_code == 200:
                if r.text.strip() != CURRENT_VERSION:
                    if messagebox.askyesno("Update", "New version found! Download?"):
                        self.do_update()
                else:
                    messagebox.showinfo("Update", "Up to date!")
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
        def play_step(index):
            if index < len(self.stroke_history):
                s = self.stroke_history[index]
                self.canvas.create_line(s['coords'], fill=s['color'], width=s['size'], capstyle=tk.ROUND)
                self.root.after(5, lambda: play_step(index + 1))
            else: self.is_replaying = False
        play_step(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
