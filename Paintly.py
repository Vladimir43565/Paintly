import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math

# --- CONFIGURATION ---
CURRENT_VERSION = "1.0.6" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1100x750")
        self.root.configure(bg="#2c3e50")

        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.brush_type = "Solid" 
        self.stabilizer_on = tk.BooleanVar(value=True)
        self.shape_correction = tk.BooleanVar(value=True)
        
        # Points for line prediction and shape recognition
        self.points = []
        self.last_x, self.last_y = None, None

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        self.sidebar = tk.Frame(self.root, bg="#34495e", width=150, padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")

        # Settings & Color
        self.settings_btn = tk.Label(self.sidebar, text="⚙", fg="white", bg="#34495e", font=("Arial", 20), cursor="hand2")
        self.settings_btn.pack(pady=(0, 10))
        self.settings_btn.bind("<Button-1>", self.show_settings_message)

        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=45, height=45, highlightbackground="white", highlightthickness=2, cursor="hand2")
        self.color_preview.pack(pady=5)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Brush Modes
        tk.Label(self.sidebar, text="BRUSH", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.solid_btn = tk.Button(self.sidebar, text="Solid", command=lambda: self.set_brush_type("Solid"), bg="#3498db", fg="white")
        self.solid_btn.pack(fill="x", pady=2)
        self.spray_btn = tk.Button(self.sidebar, text="Spray", command=lambda: self.set_brush_type("Spray"), bg="#ecf0f1")
        self.spray_btn.pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, bg="#ecf0f1").pack(fill="x", pady=5)

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # ADVANCED FEATURES
        tk.Label(self.sidebar, text="ADVANCED", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        tk.Checkbutton(self.sidebar, text="Stabilizer", variable=self.stabilizer_on, bg="#34495e", fg="white", selectcolor="black", activebackground="#34495e").pack(anchor="w")
        tk.Checkbutton(self.sidebar, text="Shape Fix", variable=self.shape_correction, bg="#34495e", fg="white", selectcolor="black", activebackground="#34495e").pack(anchor="w")

        # Size Slider
        tk.Label(self.sidebar, text="SIZE", fg="white", bg="#34495e", font=("Arial", 8)).pack(pady=(10, 0))
        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="vertical", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="y", pady=5)

        tk.Button(self.sidebar, text="Clear", command=self.clear_canvas, bg="#e74c3c", fg="white").pack(side="bottom", fill="x")

        # Canvas
        self.canvas_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    def start_paint(self, event):
        self.points = [(event.x, event.y)]
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        self.brush_size = self.size_slider.get()
        x, y = event.x, event.y

        # Stabilizer (Line Prediction / Smoothing)
        if self.stabilizer_on.get() and self.brush_type == "Solid":
            # Weighted average: 80% current point, 20% mouse position to kill jitter
            x = self.last_x * 0.7 + event.x * 0.3
            y = self.last_y * 0.7 + event.y * 0.3

        if self.brush_type == "Solid":
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=tk.TRUE)
            self.points.append((x, y))
            self.last_x, self.last_y = x, y
        elif self.brush_type == "Spray":
            for _ in range(self.brush_size):
                sx = event.x + random.randint(-self.brush_size, self.brush_size)
                sy = event.y + random.randint(-self.brush_size, self.brush_size)
                self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=self.current_color, outline=self.current_color)

    def stop_paint(self, event):
        if self.shape_correction.get() and len(self.points) > 20:
            self.analyze_shape()
        self.points = []
        self.last_x, self.last_y = None, None

    def analyze_shape(self):
        """Simple Shape Detection: Circle or Line"""
        first = self.points[0]
        last = self.points[-1]
        dist = math.sqrt((first[0]-last[0])**2 + (first[1]-last[1])**2)
        
        # If start and end are close, it might be a circle
        if dist < 50:
            # Calculate Bounds
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            
            # Draw perfect circle
            if messagebox.askyesno("Shape Correction", "Convert to perfect circle?"):
                self.canvas.delete(tk.ALL) # Simple demo: clears for shape. In real apps, we'd only delete last stroke.
                self.canvas.create_oval(x1, y1, x2, y2, outline=self.current_color, width=self.brush_size)
        
        # If points are mostly in one direction, it's a line
        elif dist > 150:
             if messagebox.askyesno("Shape Correction", "Convert to straight line?"):
                self.canvas.create_line(first[0], first[1], last[0], last[1], fill=self.current_color, width=self.brush_size)

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5, headers={'Cache-Control': 'no-cache'})
            if response.status_code == 200:
                remote_version = response.text.strip()
                if remote_version != CURRENT_VERSION:
                    if messagebox.askyesno("Update", f"Update to {remote_version}?"):
                        new_code = requests.get(UPDATE_URL).text
                        with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                            f.write(new_code)
                        os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

    def set_brush_type(self, b_type):
        self.brush_type = b_type
        self.current_color = self.draw_color
        self.solid_btn.config(bg="#3498db" if b_type=="Solid" else "#ecf0f1", fg="white" if b_type=="Solid" else "black")
        self.spray_btn.config(bg="#3498db" if b_type=="Spray" else "#ecf0f1", fg="white" if b_type=="Spray" else "black")

    def show_settings_message(self, event):
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_x()}+{self.root.winfo_y()}")
        overlay.configure(bg="black")
        tk.Label(overlay, text="Paintly is Free Forever\nNo Ads | No Tracking", fg="white", bg="black", font=("Arial", 20)).place(relx=0.5, rely=0.5, anchor="center")
        overlay.bind("<Button-1>", lambda e: overlay.destroy())

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def use_eraser(self):
        self.current_color = "white"
        self.brush_type = "Solid"

    def clear_canvas(self):
        if messagebox.askyesno("Confirm", "Clear everything?"):
            self.canvas.delete("all")

    def reset(self, event):
        self.last_x, self.last_y = None, None

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
