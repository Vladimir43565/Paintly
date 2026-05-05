import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk
import requests
import sys
import os
import random
import webbrowser
import time

# --- CONFIGURATION ---
CURRENT_VERSION = "1.2.9" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"
DISCORD_LINK = "https://discord.gg/3YCAwptj6d"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Workstation Pro")
        self.root.geometry("1500x950")
        
        # Professional Workstation Palette
        self.clr_bg = "#2b2b2b"      
        self.clr_panel = "#3c3f41"   
        self.clr_active = "#4e5154"  
        self.clr_accent = "#4083d1"  
        self.clr_text = "#bbbbbb"
        self.clr_border = "#212121"
        self.canvas_bg = "#1e1e1e"
        
        self.draw_color = "#4083d1"
        self.brush_size = 20
        self.brush_opacity = 1.0
        self.brush_type = "Ink Pen"
        
        self.master_history = [] 
        self.undo_stack = [] 
        self.current_stroke_ids = []
        self.current_stroke_data = []
        
        self.is_replaying = False
        self.stabilize_factor = 0.1
        
        self.setup_ui()

    def setup_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.configure(bg=self.clr_bg)

        # 1. TOP MENU BAR
        self.menu_bar = tk.Frame(self.root, bg=self.clr_panel, height=30, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.menu_bar.pack(side="top", fill="x")
        
        menu_items = ["File", "Edit", "View", "Image", "Layer", "Select", "Filter", "Tools", "Settings", "Window", "Help"]
        for item in menu_items:
            tk.Label(self.menu_bar, text=item, fg=self.clr_text, bg=self.clr_panel, font=("Segoe UI", 9), padx=10).pack(side="left")

        # 2. BRUSH PROPERTIES TOOLBAR (Top)
        self.tool_props = tk.Frame(self.root, bg=self.clr_panel, height=45, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.tool_props.pack(side="top", fill="x")
        
        tk.Label(self.tool_props, text=" Brush Presets: ", fg=self.clr_text, bg=self.clr_panel, font=("Segoe UI", 9)).pack(side="left", padx=(10,0))
        self.brush_select = ttk.Combobox(self.tool_props, values=["Pencil", "Ink Pen", "Marker", "Airbrush", "Eraser"], width=15)
        self.brush_select.set(self.brush_type)
        self.brush_select.pack(side="left", padx=5)
        self.brush_select.bind("<<ComboboxSelected>>", lambda e: self.set_brush(self.brush_select.get()))

        tk.Label(self.tool_props, text=" Opacity: ", fg=self.clr_text, bg=self.clr_panel, font=("Segoe UI", 9)).pack(side="left", padx=(10,0))
        self.opac_slider = tk.Scale(self.tool_props, from_=0.1, to=1.0, resolution=0.1, orient="horizontal", length=100, bg=self.clr_panel, fg=self.clr_text, highlightthickness=0, bd=0, showvalue=False)
        self.opac_slider.set(self.brush_opacity)
        self.opac_slider.pack(side="left")

        tk.Label(self.tool_props, text=" Size: ", fg=self.clr_text, bg=self.clr_panel, font=("Segoe UI", 9)).pack(side="left", padx=(10,0))
        self.size_spin = tk.Spinbox(self.tool_props, from_=1, to=1000, width=5, bg=self.clr_bg, fg=self.clr_text, bd=0)
        self.size_spin.pack(side="left", padx=5)
        self.size_spin.delete(0, "end")
        self.size_spin.insert(0, str(self.brush_size))

        # 3. RIGHT DOCKER (Color & Layers)
        self.docker = tk.Frame(self.root, bg=self.clr_panel, width=300, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.docker.pack(side="right", fill="y")
        self.docker.pack_propagate(False)

        # Advanced Color Selector Area
        tk.Label(self.docker, text="Advanced Color Selector", bg=self.clr_active, fg="white", font=("Segoe UI", 8, "bold"), pady=4).pack(fill="x")
        self.color_ring_sim = tk.Frame(self.docker, bg=self.clr_panel, height=200)
        self.color_ring_sim.pack(fill="x", pady=10)
        
        self.active_color_btn = tk.Button(self.color_ring_sim, bg=self.draw_color, width=15, height=2, command=self.change_color, relief="flat", bd=2, highlightbackground=self.clr_border)
        self.active_color_btn.pack(pady=40)

        # Layers Stack Area
        tk.Label(self.docker, text="Layers", bg=self.clr_active, fg="white", font=("Segoe UI", 8, "bold"), pady=4).pack(fill="x")
        self.layer_frame = tk.Frame(self.docker, bg=self.clr_bg, height=300, bd=1, highlightbackground=self.clr_border)
        self.layer_frame.pack(fill="x", padx=5, pady=5)
        
        # Simulating Layer Stack
        for layer_name in ["Paint Layer 2", "Paint Layer 1", "Background"]:
            f = tk.Frame(self.layer_frame, bg=self.clr_active if "2" in layer_name else self.clr_panel, height=30, bd=1, highlightbackground=self.clr_border)
            f.pack(fill="x", pady=1)
            tk.Label(f, text=f"👁 {layer_name}", fg=self.clr_text, bg=f["bg"], font=("Segoe UI", 9)).pack(side="left", padx=5)

        # Playback/Recording
        tk.Label(self.docker, text="Recorder", bg=self.clr_active, fg="white", font=("Segoe UI", 8, "bold"), pady=4).pack(fill="x", pady=(10,0))
        tk.Button(self.docker, text="● START PLAYBACK", command=self.run_replay, bg="#a62b2b", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), pady=8).pack(fill="x", padx=10, pady=10)
        
        # 4. TOOLBOX (Left Slim Bar)
        self.toolbox = tk.Frame(self.root, bg=self.clr_panel, width=40, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.toolbox.pack(side="left", fill="y")
        
        tool_icons = ["Selection", "✎", "🖋", "🖌", "Bucket", "Gradient", "Text", "⌫"]
        for icon in tool_icons:
            tk.Button(self.toolbox, text=icon, bg=self.clr_panel, fg=self.clr_text, relief="flat", width=3, pady=5).pack()

        # 5. CANVAS WORKSPACE
        self.workspace = tk.Frame(self.root, bg=self.clr_bg)
        self.workspace.pack(side="left", fill="both", expand=True)
        
        # The actual canvas sheet
        self.canvas = tk.Canvas(self.workspace, bg=self.canvas_bg, highlightthickness=0, cursor="crosshair")
        self.canvas.place(relx=0.5, rely=0.5, anchor="center", width=1000, height=800)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def change_color(self):
        c = askcolor(color=self.draw_color)[1]
        if c:
            self.draw_color = c
            self.active_color_btn.configure(bg=c)

    def set_brush(self, b_name):
        self.brush_type = b_name

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_stroke_ids = []
        self.current_stroke_data = []
        self.last_time = time.time()

    def paint(self, event):
        if self.is_replaying: return
        now = time.time()
        delta = now - self.last_time
        
        sz = int(self.size_spin.get())
        opac = self.opac_slider.get()
        
        color = self.draw_color if "Eraser" not in self.brush_type else self.canvas_bg
        
        line_id = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width=sz, fill=color, capstyle=tk.ROUND, smooth=True)
        self.current_stroke_ids.append(line_id)
        self.current_stroke_data.append({'coords': (self.last_x, self.last_y, event.x, event.y), 'color': color, 'size': sz, 'delay': delta})
        
        self.last_x, self.last_y = event.x, event.y
        self.last_time = now

    def stop_draw(self, event):
        if self.current_stroke_ids:
            self.undo_stack.append(self.current_stroke_ids)
            self.master_history.append({'type': 'stroke', 'data': self.current_stroke_data})

    def run_replay(self):
        if not self.master_history or self.is_replaying: return
        self.is_replaying = True
        self.canvas.delete("all")
        
        def play_step(s_idx, p_idx):
            if s_idx < len(self.master_history):
                stroke = self.master_history[s_idx]
                pts = stroke['data']
                if p_idx < len(pts):
                    p = pts[p_idx]
                    self.canvas.create_line(p['coords'], fill=p['color'], width=p['size'], capstyle=tk.ROUND)
                    wait = int(p['delay'] * 1000)
                    self.root.after(max(1, wait), lambda: play_step(s_idx, p_idx + 1))
                else:
                    self.root.after(150, lambda: play_step(s_idx + 1, 0))
            else: self.is_replaying = False
        play_step(0, 0)

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
