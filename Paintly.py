import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math

# --- CONFIGURATION ---
CURRENT_VERSION = "1.1.2" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1200x850")
        self.root.configure(bg="#2c3e50")

        # Drawing State
        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.brush_type = "Solid" 
        
        # Stroke Recording (For Replay)
        self.stroke_history = [] 
        self.is_replaying = False
        
        self.stabilizer_on = tk.BooleanVar(value=True)
        self.shape_correction = tk.BooleanVar(value=True)
        
        self.points = []
        self.last_x, self.last_y = None, None

        self.setup_ui()
        # Check for updates 1 second after launch
        self.root.after(1000, self.check_for_updates)

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#34495e", width=200, padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")

        # Color Preview
        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=45, height=45, highlightbackground="white", highlightthickness=2, cursor="hand2")
        self.color_preview.pack(pady=5)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # REPLAY SYSTEM
        tk.Label(self.sidebar, text="REPLAY ENGINE", fg="#f1c40f", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.replay_btn = tk.Button(self.sidebar, text="▶ Watch Replay", command=self.run_replay, bg="#27ae60", fg="white", relief="flat")
        self.replay_btn.pack(fill="x", pady=2)

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Tools
        tk.Label(self.sidebar, text="BRUSH TOOLS", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        tk.Button(self.sidebar, text="Solid Brush", command=lambda: self.set_brush_type("Solid"), bg="#3498db", fg="white", relief="flat").pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, bg="#ecf0f1", relief="flat").pack(fill="x", pady=2)

        # Size Slider
        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="horizontal", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="x", pady=10)

        tk.Button(self.sidebar, text="Clear All", command=self.clear_canvas, bg="#e74c3c", fg="white", relief="flat").pack(side="bottom", fill="x")

        # Canvas
        self.canvas_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def start_draw(self, event):
        if self.is_replaying: return
        self.points = [(event.x, event.y)]
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        if self.is_replaying: return
        self.brush_size = self.size_slider.get()
        x, y = event.x, event.y

        if self.stabilizer_on.get():
            x = self.last_x * 0.7 + event.x * 0.3
            y = self.last_y * 0.7 + event.y * 0.3

        # Draw and Save to History
        self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=tk.TRUE)
        self.stroke_history.append({
            'coords': (self.last_x, self.last_y, x, y),
            'color': self.current_color,
            'size': self.brush_size
        })
        
        self.last_x, self.last_y = x, y

    def stop_draw(self, event):
        self.points = []

    def run_replay(self):
        if not self.stroke_history or self.is_replaying: return
        
        self.is_replaying = True
        self.canvas.delete("all")
        
        def play_step(index):
            if index < len(self.stroke_history):
                s = self.stroke_history[index]
                self.canvas.create_line(s['coords'], fill=s['color'], width=s['size'], capstyle=tk.ROUND)
                self.root.after(5, lambda: play_step(index + 1))
            else:
                self.is_replaying = False

        play_step(0)

    def check_for_updates(self):
        try:
            # Force cache bypass
            r = requests.get(VERSION_URL, timeout=5, headers={'Cache-Control': 'no-cache'})
            if r.status_code == 200:
                remote_v = r.text.strip()
                if remote_v != CURRENT_VERSION:
                    if messagebox.askyesno("Update", f"New Version {remote_v} available! Update?"):
                        self.do_update()
        except: pass

    def do_update(self):
        try:
            new_code = requests.get(UPDATE_URL).text
            if "class PaintlyApp" in new_code:
                with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                    f.write(new_code)
                os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def set_brush_type(self, b_type):
        self.current_color = self.draw_color

    def use_eraser(self):
        self.current_color = "white"

    def clear_canvas(self):
        if messagebox.askyesno("Clear", "Clear drawing and history?"):
            self.canvas.delete("all")
            self.stroke_history = []

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
