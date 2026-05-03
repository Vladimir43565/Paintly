import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk
import requests
import sys
import os
import random
import webbrowser

# --- CONFIGURATION ---
CURRENT_VERSION = "1.2.3" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"
DISCORD_LINK = "https://discord.gg/3YCAwptj6d"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Creative")
        self.root.geometry("1400x950")
        
        # Theme & Engine
        self.dark_mode = True 
        self.set_theme_colors()
        
        self.draw_color = "#6366f1"
        self.brush_size = 10
        self.brush_flow = 0.6    
        self.brush_type = "Ink" 
        
        # Tracking for Undo/Redo & Replay
        self.stroke_history = [] 
        self.current_stroke_ids = [] # IDs of items in the current continuous stroke
        self.undo_stack = [] # List of lists (each sub-list is one full stroke)
        
        self.is_replaying = False
        self.stabilize_factor = 0.15 
        
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

        # 1. TOP HEADER
        self.header = tk.Frame(self.root, bg=self.clr_side, height=60, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.header.pack(side="top", fill="x")

        tk.Label(self.header, text=f"Paintly Studio v{CURRENT_VERSION}", fg=self.clr_accent, bg=self.clr_side, font=("Segoe UI", 14, "bold")).pack(side="left", padx=25)
        
        # Quick Actions in Header
        tk.Button(self.header, text="↩ Undo Last", command=self.undo, bg=self.clr_side, fg=self.clr_text, relief="flat", padx=10).pack(side="left", padx=5)
        tk.Button(self.header, text="🖼 Import Image", command=self.import_image, bg=self.clr_accent, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15).pack(side="left", padx=20)

        self.update_btn = tk.Button(self.header, text="Check Updates", command=self.manual_update_check, 
                                   bg=self.clr_side, fg=self.clr_accent, relief="flat", font=("Segoe UI", 9, "bold"), padx=12)
        self.update_btn.pack(side="right", padx=20, pady=10)

        # 2. SIDEBAR
        self.sidebar = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=20)
        self.sidebar.pack(side="left", fill="y")

        self.tools = tk.Frame(self.sidebar, bg=self.clr_side, padx=15, pady=20, highlightthickness=1, highlightbackground=self.clr_border)
        self.tools.pack(fill="y", expand=True)

        # Color
        tk.Label(self.tools, text="COLOR", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8, "bold")).pack(pady=(0,5))
        self.color_preview = tk.Frame(self.tools, bg=self.draw_color, width=50, height=50, cursor="hand2", highlightthickness=2, highlightbackground=self.clr_border)
        self.color_preview.pack(pady=(0, 20))
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        # Brushes
        brushes = [("Pencil", "✏"), ("Soft", "🖌"), ("Ink", "🖋"), ("Spray", "✨"), ("Eraser", "🧽")]
        for name, icon in brushes:
            btn = tk.Button(self.tools, text=f"{icon}  {name}", command=lambda n=name: self.set_brush(n),
                            bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 10), 
                            relief="flat", anchor="w", padx=10, pady=8, activebackground=self.clr_accent)
            btn.pack(fill="x")

        self.add_divider()

        # ENGINE
        tk.Label(self.tools, text="ENGINE", bg=self.clr_side, fg=self.clr_accent, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        
        tk.Label(self.tools, text="Size", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))
        self.size_slider = tk.Scale(self.tools, from_=1, to=150, orient="horizontal", bg=self.clr_side, highlightthickness=0, fg=self.clr_text)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="x")

        tk.Label(self.tools, text="Flow", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))
        self.flow_slider = tk.Scale(self.tools, from_=0.1, to=1.0, resolution=0.1, orient="horizontal", bg=self.clr_side, highlightthickness=0, fg=self.clr_text)
        self.flow_slider.set(self.brush_flow)
        self.flow_slider.pack(fill="x")

        self.add_divider()

        tk.Button(self.tools, text="▶ Playback", command=self.run_replay, bg=self.clr_accent, fg="white", relief="flat", font=("Segoe UI", 10, "bold"), pady=8).pack(fill="x")
        
        theme_txt = "☀️ Light" if self.dark_mode else "🌙 Dark"
        tk.Button(self.tools, text=theme_txt, command=self.toggle_theme, bg=self.clr_bg, fg=self.clr_text, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=10)

        # 3. CANVAS
        self.canvas_frame = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.canvas_bg, highlightthickness=0, cursor="pencil")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def add_divider(self):
        tk.Frame(self.tools, bg=self.clr_border, height=1).pack(fill="x", pady=20)

    def import_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            img = Image.open(file_path)
            # Resize to fit canvas roughly
            img.thumbnail((800, 600))
            self.tk_img = ImageTk.PhotoImage(img)
            img_id = self.canvas.create_image(400, 300, image=self.tk_img)
            self.undo_stack.append([img_id]) # Add to undo stack as a single item

    def undo(self):
        if self.undo_stack:
            last_stroke = self.undo_stack.pop()
            for item_id in last_stroke:
                self.canvas.delete(item_id)
            # Clean up history for replay as well
            if self.stroke_history:
                # This is a simple pop; for perfect replay undo, complex filtering is needed
                self.stroke_history = self.stroke_history[:-len(last_stroke)]

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.set_theme_colors()
        self.setup_ui()

    def set_brush(self, b_name):
        self.brush_type = b_name

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_stroke_ids = []

    def paint(self, event):
        if self.is_replaying: return
        
        current_sz = self.size_slider.get()
        alpha = self.stabilize_factor
        
        cur_x = alpha * event.x + (1 - alpha) * self.last_x
        cur_y = alpha * event.y + (1 - alpha) * self.last_y
        
        color = self.draw_color if self.brush_type != "Eraser" else self.canvas_bg
        flow = self.flow_slider.get()
        
        line_id = None
        if self.brush_type == "Soft":
            for i in range(2):
                sz = current_sz + (i * 6)
                line_id = self.canvas.create_line(self.last_x, self.last_y, cur_x, cur_y, width=sz, fill=color, capstyle=tk.ROUND, smooth=True)
                self.current_stroke_ids.append(line_id)
        elif self.brush_type == "Spray":
            for _ in range(int(10 * flow)):
                offset = current_sz * 1.5
                sx = cur_x + random.randint(-int(offset), int(offset))
                sy = cur_y + random.randint(-int(offset), int(offset))
                dot_id = self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=color, outline="")
                self.current_stroke_ids.append(dot_id)
        else:
            line_id = self.canvas.create_line(self.last_x, self.last_y, cur_x, cur_y, width=current_sz, fill=color, capstyle=tk.ROUND, smooth=True)
            self.current_stroke_ids.append(line_id)

        self.stroke_history.append({'coords': (self.last_x, self.last_y, cur_x, cur_y), 'color': color, 'size': current_sz})
        self.last_x, self.last_y = cur_x, cur_y

    def stop_draw(self, event):
        if self.current_stroke_ids:
            self.undo_stack.append(self.current_stroke_ids)

    def run_replay(self):
        if not self.stroke_history or self.is_replaying: return
        self.is_replaying = True
        self.canvas.delete("all")
        def play(i):
            if i < len(self.stroke_history):
                s = self.stroke_history[i]
                self.canvas.create_line(s['coords'], fill=s['color'], width=s['size'], capstyle=tk.ROUND)
                self.root.after(5, lambda: play(i+1))
            else: self.is_replaying = False
        play(0)

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.color_preview.configure(bg=selected)

    def manual_update_check(self):
        try:
            cb = random.randint(100000, 999999)
            r = requests.get(f"{VERSION_URL}?nocache={cb}", timeout=5)
            if r.status_code == 200:
                remote_v = r.text.strip()
                remote_parts = [int(p) for p in remote_v.split('.')]
                local_parts = [int(p) for p in CURRENT_VERSION.split('.')]
                if remote_parts > local_parts:
                    if messagebox.askyesno("Update", f"v{remote_v} is available!"):
                        self.do_update()
                else: messagebox.showinfo("Paintly", "Version is up to date.")
        except: pass

    def do_update(self):
        try:
            cb = random.randint(100000, 999999)
            new_code = requests.get(f"{UPDATE_URL}?nocache={cb}").text
            with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                f.write(new_code)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
