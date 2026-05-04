import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk
import requests
import sys
import os
import random
import time

# --- CONFIGURATION ---
CURRENT_VERSION = "1.2.7" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Creative")
        self.root.geometry("1400x950")
        
        self.dark_mode = True 
        self.set_theme_colors()
        
        self.draw_color = "#6366f1"
        self.brush_size = 10
        self.brush_type = "Ink" 
        
        # Chronological storage for 1:1 playback
        self.master_history = [] 
        self.undo_stack = [] 
        
        self.is_replaying = False
        self.stabilize_factor = 0.2 
        
        self.setup_ui()

    def set_theme_colors(self):
        if self.dark_mode:
            self.clr_bg = "#0f172a"      
            self.clr_side = "#1e293b"    
            self.clr_accent = "#818cf8"  
            self.clr_text = "#f8fafc"
            self.clr_border = "#334155"
            self.canvas_bg = "#1e293b"
        else:
            self.clr_bg = "#f8fafc"      
            self.clr_side = "#ffffff"    
            self.clr_accent = "#4f46e5"  
            self.clr_text = "#1e293b"
            self.clr_border = "#e2e8f0"
            self.canvas_bg = "#ffffff"

    def setup_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.configure(bg=self.clr_bg)

        # HEADER
        self.header = tk.Frame(self.root, bg=self.clr_side, height=65, highlightthickness=1, highlightbackground=self.clr_border)
        self.header.pack(side="top", fill="x")

        tk.Label(self.header, text="PAINTLY", fg=self.clr_accent, bg=self.clr_side, font=("Inter", 16, "bold")).pack(side="left", padx=25)
        
        tk.Button(self.header, text=" ⎌  Undo ", command=self.undo, bg=self.clr_side, fg=self.clr_text, relief="flat", font=("Inter", 10)).pack(side="left", padx=10)
        tk.Button(self.header, text=" ⊞  Import ", command=self.import_image, bg=self.clr_accent, fg="white", relief="flat", font=("Inter", 10, "bold"), padx=15).pack(side="left", padx=10)

        # SIDEBAR
        self.sidebar = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=20)
        self.sidebar.pack(side="left", fill="y")

        self.tools = tk.Frame(self.sidebar, bg=self.clr_side, padx=12, pady=20, highlightthickness=1, highlightbackground=self.clr_border)
        self.tools.pack(fill="y", expand=True)

        # Color
        self.color_preview = tk.Frame(self.tools, bg=self.draw_color, width=50, height=50, highlightthickness=2, highlightbackground=self.clr_border)
        self.color_preview.pack(pady=10)
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        # Brushes
        for name, icon in [("Pencil", "✎"), ("Ink Pen", "🖋"), ("Eraser", "⌫")]:
            tk.Button(self.tools, text=f"{icon} {name}", command=lambda n=name: self.set_brush(n),
                      bg=self.clr_side, fg=self.clr_text, font=("Inter", 10), relief="flat", anchor="w", padx=10).pack(fill="x", pady=2)

        self.create_styled_slider("Size", self.brush_size, 1, 100, "size_slider")

        # Playback Action
        tk.Button(self.tools, text=" ▷ Playback Real-Time", command=self.run_replay, bg=self.clr_accent, fg="white", relief="flat", font=("Inter", 10, "bold"), pady=10).pack(fill="x", pady=20)

        # CANVAS
        self.canvas_frame = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.canvas_bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def create_styled_slider(self, label, start_val, f, t, attr_name):
        tk.Label(self.tools, text=label, bg=self.clr_side, fg=self.clr_text).pack(anchor="w", padx=5, pady=(10,0))
        slider = tk.Scale(self.tools, from_=f, to=t, orient="horizontal", bg=self.clr_side, fg=self.clr_text, highlightthickness=0)
        slider.set(start_val)
        slider.pack(fill="x")
        setattr(self, attr_name, slider)

    def import_image(self):
        f = filedialog.askopenfilename()
        if f:
            img = Image.open(f)
            img.thumbnail((600, 400))
            self.tk_img = ImageTk.PhotoImage(img)
            img_id = self.canvas.create_image(400, 300, image=self.tk_img)
            self.master_history.append({'type': 'image', 'ref': self.tk_img, 'pos': (400, 300)})
            self.undo_stack.append([img_id])

    def undo(self):
        if self.undo_stack:
            for item in self.undo_stack.pop(): self.canvas.delete(item)
            if self.master_history: self.master_history.pop()

    def set_brush(self, b_name): self.brush_type = b_name

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.stroke_ids = []
        self.stroke_data = []
        self.last_time = time.time()

    def paint(self, event):
        if self.is_replaying: return
        
        now = time.time()
        delta = now - self.last_time
        
        cur_sz = self.size_slider.get()
        color = self.draw_color if self.brush_type != "Eraser" else self.canvas_bg
        
        line_id = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          width=cur_sz, fill=color, capstyle=tk.ROUND, smooth=True)
        
        self.stroke_ids.append(line_id)
        self.stroke_data.append({'coords': (self.last_x, self.last_y, event.x, event.y), 'color': color, 'size': cur_sz, 'delay': delta})
        
        self.last_x, self.last_y = event.x, event.y
        self.last_time = now

    def stop_draw(self, event):
        if self.stroke_ids:
            self.undo_stack.append(self.stroke_ids)
            self.master_history.append({'type': 'stroke', 'data': self.stroke_data})

    def run_replay(self):
        if not self.master_history or self.is_replaying: return
        self.is_replaying = True
        self.canvas.delete("all")
        
        def play_step(s_idx, p_idx):
            if s_idx < len(self.master_history):
                stroke = self.master_history[s_idx]
                if stroke['type'] == 'image':
                    self.canvas.create_image(stroke['pos'], image=stroke['ref'])
                    self.root.after(300, lambda: play_step(s_idx + 1, 0))
                else:
                    pts = stroke['data']
                    if p_idx < len(pts):
                        p = pts[p_idx]
                        self.canvas.create_line(p['coords'], fill=p['color'], width=p['size'], capstyle=tk.ROUND)
                        # Fixed: Uses actual recorded time deltas for realistic movement
                        wait = int(p['delay'] * 1000)
                        self.root.after(max(1, wait), lambda: play_step(s_idx, p_idx + 1))
                    else:
                        self.root.after(200, lambda: play_step(s_idx + 1, 0))
            else:
                self.is_replaying = False

        play_step(0, 0)

    def change_color(self):
        c = askcolor(color=self.draw_color)[1]
        if c:
            self.draw_color = c
            self.color_preview.configure(bg=c)

    def manual_update_check(self): pass # Logic from previous versions

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
