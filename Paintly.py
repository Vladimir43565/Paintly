import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import math

# --- CONFIGURATION ---
CURRENT_VERSION = "1.0.9" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1200x850")
        self.root.configure(bg="#2c3e50")

        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.brush_type = "Solid" 
        
        # Color History
        self.color_history = ["#000000", "#ffffff", "#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6"]
        
        # Layer Management
        self.layers = {"Background": [], "Foreground": []}
        self.active_layer = "Foreground"
        
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

        # Active Color & History
        self.settings_btn = tk.Label(self.sidebar, text="⚙", fg="white", bg="#34495e", font=("Arial", 20), cursor="hand2")
        self.settings_btn.pack(pady=(0, 5))
        self.settings_btn.bind("<Button-1>", self.show_settings_message)

        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=50, height=50, highlightbackground="white", highlightthickness=2, cursor="hand2")
        self.color_preview.pack(pady=5)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        self.history_frame = tk.Frame(self.sidebar, bg="#34495e")
        self.history_frame.pack(pady=5)
        self.update_history_ui()

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # LAYER CONTROL (New in 1.0.9)
        tk.Label(self.sidebar, text="LAYERS", fg="#ecf0f1", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.layer_var = tk.StringVar(value="Foreground")
        tk.Radiobutton(self.sidebar, text="Foreground", variable=self.layer_var, value="Foreground", bg="#34495e", fg="white", selectcolor="#2c3e50", command=self.switch_layer).pack(anchor="w")
        tk.Radiobutton(self.sidebar, text="Background", variable=self.layer_var, value="Background", bg="#34495e", fg="white", selectcolor="#2c3e50", command=self.switch_layer).pack(anchor="w")

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Brush Selection
        tk.Label(self.sidebar, text="BRUSH", fg="white", bg="#34495e", font=("Arial", 8, "bold")).pack()
        self.solid_btn = tk.Button(self.sidebar, text="Solid", command=lambda: self.set_brush_type("Solid"), bg="#3498db", fg="white", relief="flat")
        self.solid_btn.pack(fill="x", pady=2)
        self.spray_btn = tk.Button(self.sidebar, text="Spray", command=lambda: self.set_brush_type("Spray"), bg="#ecf0f1", relief="flat")
        self.spray_btn.pack(fill="x", pady=2)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, bg="#ecf0f1", relief="flat").pack(fill="x", pady=5)

        # Features & Size
        tk.Checkbutton(self.sidebar, text="Stabilizer", variable=self.stabilizer_on, bg="#34495e", fg="white", selectcolor="black").pack(anchor="w")
        tk.Checkbutton(self.sidebar, text="Shape Fix", variable=self.shape_correction, bg="#34495e", fg="white", selectcolor="black").pack(anchor="w")
        
        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="horizontal", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="x", pady=10)

        tk.Button(self.sidebar, text="Clear Canvas", command=self.clear_canvas, bg="#e74c3c", fg="white", relief="flat").pack(side="bottom", fill="x")

        # Canvas Area
        self.canvas_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def switch_layer(self):
        self.active_layer = self.layer_var.get()

    def update_history_ui(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        for color in self.color_history:
            btn = tk.Frame(self.history_frame, bg=color, width=22, height=22, highlightbackground="gray", highlightthickness=1, cursor="hand2")
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
            if selected not in self.color_history:
                self.color_history.insert(0, selected)
                self.color_history = self.color_history[:7]
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
            # Tag the item with the current layer name
            item = self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=self.current_color, capstyle=tk.ROUND, smooth=tk.TRUE, tags=self.active_layer)
            self.points.append((x, y))
            self.last_x, self.last_y = x, y
        elif self.brush_type == "Spray":
            for _ in range(self.brush_size):
                sx = event.x + random.randint(-self.brush_size, self.brush_size)
                sy = event.y + random.randint(-self.brush_size, self.brush_size)
                self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=self.current_color, outline=self.current_color, tags=self.active_layer)

        # Ensure Foreground is always on top visually
        self.canvas.tag_raise("Foreground")

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
                self.canvas.create_oval(min(xs), min(ys), max(xs), max(ys), outline=self.current_color, width=self.brush_size, tags=self.active_layer)
        elif dist > 100:
            if messagebox.askyesno("Shape Correction", "Snap to straight line?"):
                self.canvas.create_line(first[0], first[1], last[0], last[1], fill=self.current_color, width=self.brush_size, tags=self.active_layer)
        self.canvas.tag_raise("Foreground")

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5, headers={'Cache-Control': 'no-cache'})
            if response.status_code == 200:
                remote_version = response.text.strip()
                if remote_version != CURRENT_VERSION:
                    if messagebox.askyesno("Update", f"Update Paintly to {remote_version}?"):
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
        tk.Label(overlay, text="Paintly v1.0.9\nFree & Professional", fg="white", bg="black", font=("Arial", 20)).place(relx=0.5, rely=0.5, anchor="center")
        overlay.bind("<Button-1>", lambda e: overlay.destroy())

    def use_eraser(self):
        self.current_color = "white"
        self.brush_type = "Solid"

    def clear_canvas(self):
        if messagebox.askyesno("Confirm", "Clear everything?"):
            self.canvas.delete("all")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
