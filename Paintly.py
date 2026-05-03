import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math
import time

# --- CONFIGURATION ---
CURRENT_VERSION = "1.1.0" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1200x850")
        self.root.configure(bg="#2c3e50")

        # Core Drawing Vars
        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.brush_type = "Solid" 
        self.active_layer = "Foreground"
        
        # RECORDING DATA (New in 1.1.0)
        self.stroke_history = []  # Stores list of: {'type': 'line', 'coords': (x1,y1,x2,y2), 'color': c, 'size': s, 'layer': l}
        self.is_replaying = False
        
        # Toggles
        self.stabilizer_on = tk.BooleanVar(value=True)
        self.shape_correction = tk.BooleanVar(value=True)
        
        self.points = []
        self.last_x, self.last_y = None, None

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#34495e", width=200, padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")

        # Color & History
        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=40, height=40, highlightbackground="white", highlightthickness=2)
        self.color_preview.pack(pady=5)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # REPLAY CONTROLS
        tk.Label(self.sidebar, text="REPLAY & VIDEO", fg="#f1c40f", bg="#34495e", font=("Arial", 8, "bold")).pack()
        tk.Button(self.sidebar, text="▶ Watch Replay", command=self.run_replay, bg="#27ae60", fg="white", relief="flat").pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="💾 Export GIF", command=self.export_gif_placeholder, bg="#8e44ad", fg="white", relief="flat").pack(fill="x", pady=2)

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Layers
        tk.Label(self.sidebar, text="LAYERS", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.layer_var = tk.StringVar(value="Foreground")
        tk.Radiobutton(self.sidebar, text="Foreground", variable=self.layer_var, value="Foreground", bg="#34495e", fg="white", selectcolor="#2c3e50").pack(anchor="w")
        tk.Radiobutton(self.sidebar, text="Background", variable=self.layer_var, value="Background", bg="#34495e", fg="white", selectcolor="#2c3e50").pack(anchor="w")

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Brush Controls
        self.solid_btn = tk.Button(self.sidebar, text="Solid", command=lambda: self.set_brush_type("Solid"), bg="#3498db", fg="white", relief="flat")
        self.solid_btn.pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, bg="#ecf0f1", relief="flat").pack(fill="x", pady=2)

        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="horizontal", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="x", pady=10)

        tk.Button(self.sidebar, text="Clear Canvas", command=self.clear_canvas, bg="#e74c3c", fg="white", relief="flat").pack(side="bottom", fill="x")

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
        self.active_layer = self.layer_var.get()
        x, y = event.x, event.y

        if self.stabilizer_on.get() and self.brush_type == "Solid":
            x = self.last_x * 0.7 + event.x * 0.3
            y = self.last_y * 0.7 + event.y * 0.3

        if self.brush_type == "Solid":
            # Draw line
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=tk.TRUE, tags=self.active_layer)
            
            # RECORD THE STROKE
            self.stroke_history.append({
                'type': 'line',
                'coords': (self.last_x, self.last_y, x, y),
                'color': self.current_color,
                'size': self.brush_size,
                'layer': self.active_layer
            })
            
            self.points.append((x, y))
            self.last_x, self.last_y = x, y

        self.canvas.tag_raise("Foreground")

    def stop_draw(self, event):
        self.points = []
        self.last_x, self.last_y = None, None

    def run_replay(self):
        """Replays the drawing history like a video"""
        if not self.stroke_history:
            messagebox.showinfo("Replay", "Nothing to replay yet!")
            return

        self.is_replaying = True
        self.canvas.delete("all")
        
        def play_step(index):
            if index < len(self.stroke_history):
                stroke = self.stroke_history[index]
                if stroke['type'] == 'line':
                    self.canvas.create_line(
                        stroke['coords'], 
                        fill=stroke['color'], 
                        width=stroke['size'], 
                        capstyle=tk.ROUND, 
                        tags=stroke['layer']
                    )
                self.canvas.tag_raise("Foreground")
                # Adjust speed here (ms)
                self.root.after(5, lambda: play_step(index + 1))
            else:
                self.is_replaying = False
                messagebox.showinfo("Replay", "Replay Finished!")

        play_step(0)

    def export_gif_placeholder(self):
        messagebox.showinfo("Export", "GIF Export requires 'Pillow' library.\nIn v1.1.1, we will add auto-install for this feature!")

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def set_brush_type(self, b_type):
        self.brush_type = b_type
        self.current_color = self.draw_color

    def use_eraser(self):
        self.current_color = "white"

    def clear_canvas(self):
        if messagebox.askyesno("Confirm", "Clear everything? History will be lost."):
            self.canvas.delete("all")
            self.stroke_history = []

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200 and response.text.strip() != CURRENT_VERSION:
                if messagebox.askyesno("Update", f"Update to {response.text.strip()}?"):
                    new_code = requests.get(UPDATE_URL).text
                    with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                        f.write(new_code)
                    os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
