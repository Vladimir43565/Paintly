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
CURRENT_VERSION = "1.2.8" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"
DISCORD_LINK = "https://discord.gg/3YCAwptj6d"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Studio Pro")
        self.root.geometry("1450x950")
        
        # Professional Color Palette
        self.dark_mode = True 
        self.set_theme_colors()
        
        self.draw_color = "#6366f1"
        self.brush_size = 8
        self.brush_flow = 0.7    
        self.brush_type = "Ink Pen" 
        
        # Advanced History & Playback
        self.master_history = [] 
        self.undo_stack = [] 
        self.current_stroke_ids = []
        self.current_stroke_data = []
        
        self.is_replaying = False
        self.stabilize_factor = 0.12 
        
        self.setup_ui()

    def set_theme_colors(self):
        # Professional Graphite Theme
        self.clr_bg = "#09090b"      # Deep Zinc
        self.clr_side = "#18181b"    # Sidebar Zinc
        self.clr_accent = "#6366f1"  # Indigo Primary
        self.clr_text = "#fafafa"    # Ghost White
        self.clr_muted = "#71717a"   # Muted Gray
        self.clr_border = "#27272a"  # Subtle Border
        self.canvas_bg = "#18181b"

    def setup_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.configure(bg=self.clr_bg)

        # 1. TOP NAVIGATION BAR (SLEEK)
        self.nav = tk.Frame(self.root, bg=self.clr_side, height=50, bd=0, highlightthickness=1, highlightbackground=self.clr_border)
        self.nav.pack(side="top", fill="x")

        tk.Label(self.nav, text="PAINTLY STUDIO", fg=self.clr_accent, bg=self.clr_side, font=("Inter", 12, "bold")).pack(side="left", padx=25)
        tk.Label(self.nav, text=f"PRO {CURRENT_VERSION}", fg=self.clr_muted, bg=self.clr_side, font=("Inter", 8)).pack(side="left")
        
        # Action Group
        self.btn_style = {"bg": self.clr_side, "fg": self.clr_text, "activebackground": self.clr_border, "activeforeground": self.clr_accent, "relief": "flat", "font": ("Inter", 9)}
        
        tk.Button(self.nav, text="⎌ UNDO", command=self.undo, **self.btn_style, padx=15).pack(side="left", padx=10)
        tk.Button(self.nav, text="⊞ IMPORT IMAGE", command=self.import_image, **self.btn_style, padx=15).pack(side="left")

        self.upd_btn = tk.Button(self.nav, text="⟳ UPDATE SYSTEM", command=self.manual_update_check, bg=self.clr_accent, fg="white", relief="flat", font=("Inter", 8, "bold"), padx=15)
        self.upd_btn.pack(side="right", padx=20, pady=10)

        # 2. STUDIO SIDEBAR (CLEANER GROUPS)
        self.sidebar = tk.Frame(self.root, bg=self.clr_bg, padx=12, pady=15)
        self.sidebar.pack(side="left", fill="y")

        self.panel = tk.Frame(self.sidebar, bg=self.clr_side, padx=15, pady=20, highlightthickness=1, highlightbackground=self.clr_border)
        self.panel.pack(fill="y", expand=True)

        # COLOR PICKER SECTION
        self.section_label("ACTIVE COLOR")
        self.color_box = tk.Frame(self.panel, bg=self.draw_color, width=180, height=40, cursor="hand2", highlightthickness=1, highlightbackground=self.clr_border)
        self.color_box.pack(pady=(0, 20))
        self.color_box.bind("<Button-1>", lambda e: self.change_color())

        # BRUSH PRESETS SECTION
        self.section_label("BRUSH PRESETS")
        brushes = [("Pencil", "✎"), ("Ink Pen", "🖋"), ("Marker", "🖌"), ("Airbrush", "☁"), ("Eraser", "⌫")]
        for name, icon in brushes:
            btn = tk.Button(self.panel, text=f"{icon}  {name}", command=lambda n=name: self.set_brush(n),
                            bg=self.clr_side, fg=self.clr_text, font=("Inter", 10), 
                            relief="flat", anchor="w", padx=12, pady=8, activebackground=self.clr_accent)
            btn.pack(fill="x", pady=1)

        self.add_spacer()

        # ENGINE PARAMETERS
        self.section_label("ENGINE PARAMETERS")
        self.create_slider("Brush Size", self.brush_size, 1, 150, "size_slider")
        self.create_slider("Flow Rate", self.brush_flow, 0.1, 1.0, "flow_slider")
        self.create_slider("Smoothing", self.stabilize_factor, 0.05, 1.0, "stab_slider")

        self.add_spacer()

        # FOOTER TOOLS
        tk.Button(self.panel, text="▷ START PLAYBACK 2.0", command=self.run_replay, bg=self.clr_accent, fg="white", relief="flat", font=("Inter", 9, "bold"), pady=12).pack(fill="x")
        
        discord = tk.Label(self.panel, text="Join Community Discord", fg=self.clr_muted, bg=self.clr_side, font=("Inter", 8, "underline"), cursor="hand2")
        discord.pack(pady=(20,0))
        discord.bind("<Button-1>", lambda e: webbrowser.open(DISCORD_LINK))

        # 3. WORKSPACE (CANVAS)
        self.workspace = tk.Frame(self.root, bg=self.clr_bg, padx=10, pady=10)
        self.workspace.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.workspace, bg=self.canvas_bg, highlightthickness=1, highlightbackground=self.clr_border, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def section_label(self, txt):
        tk.Label(self.panel, text=txt, bg=self.clr_side, fg=self.clr_muted, font=("Inter", 7, "bold")).pack(anchor="w", pady=(10, 5))

    def create_slider(self, label, start_val, f, t, attr_name):
        tk.Label(self.panel, text=label, bg=self.clr_side, fg=self.clr_text, font=("Inter", 8)).pack(anchor="w", pady=(8,0))
        slider = tk.Scale(self.panel, from_=f, to=t, resolution=0.01 if t<=1 else 1, orient="horizontal", 
                         bg=self.clr_side, highlightthickness=0, fg=self.clr_text, troughcolor=self.clr_bg, 
                         activebackground=self.clr_accent, bd=0, showvalue=False)
        slider.set(start_val)
        slider.pack(fill="x")
        setattr(self, attr_name, slider)

    def add_spacer(self):
        tk.Frame(self.panel, bg=self.clr_border, height=1).pack(fill="x", pady=20)

    def import_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            img = Image.open(path)
            img.thumbnail((850, 650))
            self.tk_img = ImageTk.PhotoImage(img)
            img_id = self.canvas.create_image(425, 325, image=self.tk_img)
            self.master_history.append({'type': 'image', 'ref': self.tk_img, 'pos': (425, 325)})
            self.undo_stack.append([img_id])

    def undo(self):
        if self.undo_stack:
            for item_id in self.undo_stack.pop(): self.canvas.delete(item_id)
            if self.master_history: self.master_history.pop()

    def set_brush(self, b_name): self.brush_type = b_name

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_stroke_ids = []
        self.current_stroke_data = []
        self.last_time = time.time()

    def paint(self, event):
        if self.is_replaying: return
        now = time.time()
        delta = now - self.last_time
        
        sz = self.size_slider.get()
        alpha = self.stab_slider.get()
        
        cur_x = alpha * event.x + (1 - alpha) * self.last_x
        cur_y = alpha * event.y + (1 - alpha) * self.last_y
        
        color = self.draw_color if "Eraser" not in self.brush_type else self.canvas_bg
        
        line_id = self.canvas.create_line(self.last_x, self.last_y, cur_x, cur_y, width=sz, fill=color, capstyle=tk.ROUND, smooth=True)
        self.current_stroke_ids.append(line_id)
        self.current_stroke_data.append({'coords': (self.last_x, self.last_y, cur_x, cur_y), 'color': color, 'size': sz, 'delay': delta})
        
        self.last_x, self.last_y = cur_x, cur_y
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
                if stroke['type'] == 'image':
                    self.canvas.create_image(stroke['pos'], image=stroke['ref'])
                    self.root.after(400, lambda: play_step(s_idx + 1, 0))
                else:
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

    def change_color(self):
        c = askcolor(color=self.draw_color)[1]
        if c:
            self.draw_color = c
            self.color_box.configure(bg=c)

    def manual_update_check(self):
        try:
            cb = random.randint(1000, 9999)
            r = requests.get(f"{VERSION_URL}?cb={cb}", timeout=5)
            if r.status_code == 200:
                rv = r.text.strip()
                if [int(p) for p in rv.split('.')] > [int(p) for p in CURRENT_VERSION.split('.')]:
                    if messagebox.askyesno("Update", f"Studio v{rv} found. Upgrade?"): self.do_update()
                else: messagebox.showinfo("Paintly", "System Optimized.")
        except: pass

    def do_update(self):
        try:
            code = requests.get(f"{UPDATE_URL}?cb={random.randint(1,99)}").text
            with open(os.path.abspath(sys.argv[0]), "w", encoding="utf-8") as f: f.write(code)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
