import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os
import random
import webbrowser

# --- CONFIGURATION ---
# local version must be lower than GitHub's version.txt to trigger an update
CURRENT_VERSION = "1.2.1" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"
DISCORD_LINK = "https://discord.gg/3YCAwptj6d"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Creative")
        self.root.geometry("1350x900")
        
        # Theme State
        self.dark_mode = True 
        self.set_theme_colors()
        
        # Paint Engine State
        self.draw_color = "#6366f1"
        self.brush_size = 6
        self.brush_flow = 0.6    # Simulates opacity/density
        self.brush_type = "Ink" 
        self.stroke_history = [] 
        self.is_replaying = False
        
        # Stabilizer factor (0.1 = very heavy/smooth, 1.0 = raw input)
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
        self.header = tk.Frame(self.root, bg=self.clr_side, height=55, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.header.pack(side="top", fill="x")

        tk.Label(self.header, text=f"Paintly Studio v{CURRENT_VERSION}", fg=self.clr_accent, bg=self.clr_side, font=("Segoe UI", 14, "bold")).pack(side="left", padx=25)
        
        # Update Button
        self.update_btn = tk.Button(self.header, text="Check for Updates", command=self.manual_update_check, 
                                   bg=self.clr_accent, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.update_btn.pack(side="right", padx=20, pady=10)

        # 2. SIDEBAR TOOLBOX
        self.sidebar = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=20)
        self.sidebar.pack(side="left", fill="y")

        self.tools = tk.Frame(self.sidebar, bg=self.clr_side, padx=15, pady=20, highlightthickness=1, highlightbackground=self.clr_border)
        self.tools.pack(fill="y", expand=True)

        # Color Selector
        tk.Label(self.tools, text="ACTIVE COLOR", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8, "bold")).pack(pady=(0,5))
        self.color_preview = tk.Frame(self.tools, bg=self.draw_color, width=50, height=50, cursor="hand2", highlightthickness=2, highlightbackground=self.clr_border)
        self.color_preview.pack(pady=(0, 20))
        self.color_preview.bind("<Button-1>", lambda e: self.change_color())

        # Brush Presets
        brushes = [("Pencil", "✏"), ("Soft", "🖌"), ("Ink", "🖋"), ("Spray", "✨"), ("Eraser", "🧽")]
        for name, icon in brushes:
            btn = tk.Button(self.tools, text=f"{icon}  {name}", command=lambda n=name: self.set_brush(n),
                            bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 10), 
                            relief="flat", anchor="w", padx=10, pady=8, activebackground=self.clr_accent)
            btn.pack(fill="x")

        self.add_divider()

        # Engine Sliders
        tk.Label(self.tools, text="BRUSH ENGINE", bg=self.clr_side, fg=self.clr_accent, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        
        tk.Label(self.tools, text="Flow Intensity", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))
        self.flow_slider = tk.Scale(self.tools, from_=0.1, to=1.0, resolution=0.1, orient="horizontal", bg=self.clr_side, highlightthickness=0, fg=self.clr_text)
        self.flow_slider.set(self.brush_flow)
        self.flow_slider.pack(fill="x")

        tk.Label(self.tools, text="Stabilization", bg=self.clr_side, fg=self.clr_text, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))
        self.stab_slider = tk.Scale(self.tools, from_=0.05, to=1.0, resolution=0.05, orient="horizontal", bg=self.clr_side, highlightthickness=0, fg=self.clr_text)
        self.stab_slider.set(self.stabilize_factor)
        self.stab_slider.pack(fill="x")

        self.add_divider()

        # Replay & Theme
        tk.Button(self.tools, text="▶ Watch Replay", command=self.run_replay, bg=self.clr_accent, fg="white", relief="flat", font=("Segoe UI", 10, "bold"), pady=8).pack(fill="x")
        
        theme_txt = "☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode"
        tk.Button(self.tools, text=theme_txt, command=self.toggle_theme, bg=self.clr_bg, fg=self.clr_text, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=10)
        
        # Social
        discord = tk.Label(self.tools, text="Support Discord", fg=self.clr_accent, bg=self.clr_side, font=("Segoe UI", 9, "underline"), cursor="hand2")
        discord.pack(pady=(15,0))
        discord.bind("<Button-1>", lambda e: webbrowser.open(DISCORD_LINK))

        # 3. DRAWING CANVAS
        self.canvas_frame = tk.Frame(self.root, bg=self.clr_bg, padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.canvas_bg, highlightthickness=0, cursor="pencil")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def add_divider(self):
        tk.Frame(self.tools, bg=self.clr_border, height=1).pack(fill="x", pady=20)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.set_theme_colors()
        self.setup_ui()

    def set_brush(self, b_name):
        self.brush_type = b_name

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        if self.is_replaying: return
        
        # Weighted Smoothing (Stabilization)
        alpha = self.stab_slider.get()
        cur_x = alpha * event.x + (1 - alpha) * self.last_x
        cur_y = alpha * event.y + (1 - alpha) * self.last_y
        
        color = self.draw_color if self.brush_type != "Eraser" else self.canvas_bg
        flow = self.flow_slider.get()
        
        if self.brush_type == "Soft":
            # Multiple layers to simulate a soft airbrush
            for i in range(3):
                sz = self.brush_size + (i * 4)
                self.canvas.create_line(self.last_x, self.last_y, cur_x, cur_y, width=sz, fill=color, capstyle=tk.ROUND, smooth=True)
        elif self.brush_type == "Spray":
            # Randomized particles based on flow intensity
            for _ in range(int(15 * flow)):
                offset = self.brush_size * 2
                sx = cur_x + random.randint(-offset, offset)
                sy = cur_y + random.randint(-offset, offset)
                self.canvas.create_oval(sx, sy, sx+1, sy+1, fill=color, outline="")
        else:
            # Standard Ink / Pencil
            self.canvas.create_line(self.last_x, self.last_y, cur_x, cur_y, width=self.brush_size, fill=color, capstyle=tk.ROUND, smooth=True)

        # Store for Replay
        self.stroke_history.append({'coords': (self.last_x, self.last_y, cur_x, cur_y), 'color': color, 'size': self.brush_size, 'type': self.brush_type})
        self.last_x, self.last_y = cur_x, cur_y

    def stop_draw(self, event): pass

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
            # Cache Buster ensures we get the newest file from GitHub
            cb = random.randint(1000, 9999)
            r = requests.get(f"{VERSION_URL}?cb={cb}", timeout=5)
            if r.status_code == 200:
                remote_v = r.text.strip()
                remote_parts = [int(p) for p in remote_v.split('.')]
                local_parts = [int(p) for p in CURRENT_VERSION.split('.')]
                
                if remote_parts > local_parts:
                    if messagebox.askyesno("Update", f"New Version {remote_v} found! Upgrade now?"):
                        self.do_update()
                else: 
                    messagebox.showinfo("Paintly", f"Current version v{CURRENT_VERSION} is the latest.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not check for updates: {e}")

    def do_update(self):
        try:
            cb = random.randint(1000, 9999)
            new_code = requests.get(f"{UPDATE_URL}?cb={cb}").text
            with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f:
                f.write(new_code)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
