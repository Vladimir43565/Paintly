import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math

# --- CONFIGURATION ---
CURRENT_VERSION = "1.0.7" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1100x800")
        self.root.configure(bg="#2c3e50")

        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.brush_type = "Solid" 
        
        # Color History (Stores last 7 colors)
        self.color_history = ["#000000", "#ffffff", "#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"]
        
        self.stabilizer_on = tk.BooleanVar(value=True)
        self.shape_correction = tk.BooleanVar(value=True)
        
        self.points = []
        self.last_x, self.last_y = None, None

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#34495e", width=180, padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")

        # Settings
        self.settings_btn = tk.Label(self.sidebar, text="⚙", fg="white", bg="#34495e", font=("Arial", 20), cursor="hand2")
        self.settings_btn.pack(pady=(0, 5))
        self.settings_btn.bind("<Button-1>", self.show_settings_message)

        # Active Color
        tk.Label(self.sidebar, text="ACTIVE COLOR", fg="#bdc3c7", bg="#34495e", font=("Arial", 7, "bold")).pack()
        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=50, height=50, highlightbackground="white", highlightthickness=2, cursor="hand2")
        self.color_preview.pack(pady=5)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        # COLOR HISTORY BAR
        tk.Label(self.sidebar, text="HISTORY", fg="#bdc3c7", bg="#34495e", font=("Arial", 7, "bold")).pack(pady=(10, 0))
        self.history_frame = tk.Frame(self.sidebar, bg="#34495e")
        self.history_frame.pack(pady=5)
        self.update_history_ui()

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Brush Selection
        tk.Label(self.sidebar, text="BRUSH MODE", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.solid_btn = tk.Button(self.sidebar, text="Solid", command=lambda: self.set_brush_type("Solid"), bg="#3498db", fg="white", relief="flat")
        self.solid_btn.pack(fill="x", pady=2)
        self.spray_btn = tk.Button(self.sidebar, text="Spray", command=lambda: self.set_brush_type("Spray"), bg="#ecf0f1", relief="flat")
        self.spray_btn.pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, bg="#ecf0f1", relief="flat").pack(fill="x", pady=5)

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Advanced Toggles
        tk.Checkbutton(self.sidebar, text="Stabilizer", variable=self.stabilizer_on, bg="#34495e", fg="white", selectcolor="black", activebackground="#34495e").pack(anchor="w")
        tk.Checkbutton(self.sidebar, text="Shape Fix", variable=self.shape_correction, bg="#34495e", fg="white", selectcolor="black", activebackground="#34495e").pack(anchor="w")

        # Size Slider
        tk.Label(self.sidebar, text="SIZE", fg="white", bg="#34495e", font=("Arial", 8)).pack(pady=(10, 0))
        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="vertical", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="y", pady=5)

        tk.Button(self.sidebar, text="Clear", command=self.clear_canvas, bg="#e74c3c", fg="white", relief="flat").pack(side="bottom", fill="x")

        # Canvas Area
        self.canvas_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def update_history_ui(self):
        # Clear current history display
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        # Create small squares for each color in history
        for color in self.color_history:
            btn = tk.Frame(self.history_frame, bg=color, width=20, height=20, highlightbackground="gray", highlightthickness=1, cursor="hand2")
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, c=color: self.set_color_from_history(c))

    def set_color_from_history(self, color):
        self.draw_color = color
        self.current_color = color
        self.color_preview.configure(bg=color)

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)
            
            # Add to history if it's a new color
            if selected not in self.color_history:
                self.color_history.insert(0, selected)
                self.color_history = self.color_history[:7] # Keep only last 7
                self.update_history_ui()

    def start_draw(self, event):
        self.points = [(event.x, event.y)]
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        self.brush_size = self.size_slider.get()
        x, y = event.x, event.y

        if self.stabilizer_on.get() and self.brush_type == "Solid":
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

    def stop_draw(self, event):
        if self.shape_correction.get() and len(self.points) > 15:
            self.detect_shapes()
        self.points = []
        self.last_x, self.last_y = None, None

    def detect_shapes(self):
        first, last = self.points[0], self.points[-1]
        dist = math.sqrt((first[0]-last[0])**2 + (first[1]-last[1])**2)
        if dist < 40:
            xs, ys = [p[0] for p in self.points], [p[1] for p in self.points]
            if messagebox.askyesno("Shape Correction", "Make perfect circle?"):
                self.canvas.create_oval(min(xs), min(ys), max(xs), max(ys), outline=self.current_color, width=self.brush_size)
        elif dist > 100:
            if messagebox.askyesno("Shape Correction", "Snap to straight line?"):
                self.canvas.create_line(first[0], first[1], last[0], last[1], fill=self.current_color, width=self.brush_size)

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5, headers={'Cache-Control': 'no-cache'})
            if response.status_code == 200:
                remote_version = response.text.strip()
                if remote_version != CURRENT_VERSION:
                    if messagebox.askyesno("Update", f"New version {remote_version} found! Update now?"):
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
        overlay = tk.Frame(self.root, bg="black")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Label(overlay, text="Paintly is a Free App\nNo Ads | No Payment Needed", fg="white", bg="black", font=("Arial", 20, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        overlay.bind("<Button-1>", lambda e: overlay.destroy())

    def use_eraser(self):
        self.current_color = "white"
        self.brush_type = "Solid"

    def clear_canvas(self):
        if messagebox.askyesno("Confirm", "Wipe the entire canvas?"):
            self.canvas.delete("all")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
