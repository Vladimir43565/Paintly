import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os

# --- CONFIGURATION ---
# CURRENT_VERSION is now 1.0.2
CURRENT_VERSION = "1.0.2" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/version.txt"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly Professional - v{CURRENT_VERSION}")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2c3e50")

        self.draw_color = "#000000"
        self.current_color = "#000000"
        self.brush_size = 5
        self.last_x, self.last_y = None, None

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#34495e", width=100, padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")

        # Settings Icon
        self.settings_btn = tk.Label(self.sidebar, text="⚙", fg="white", bg="#34495e", font=("Arial", 20), cursor="hand2")
        self.settings_btn.pack(pady=(0, 20))
        self.settings_btn.bind("<Button-1>", self.show_settings_message)

        tk.Label(self.sidebar, text="TOOLS", fg="white", bg="#34495e", font=("Arial", 10, "bold")).pack(pady=10)

        self.color_preview = tk.Frame(self.sidebar, bg=self.draw_color, width=40, height=40, highlightbackground="white", highlightthickness=2)
        self.color_preview.pack(pady=5)

        tk.Button(self.sidebar, text="Color", command=self.change_color, relief="flat", bg="#ecf0f1").pack(fill="x", pady=5)
        tk.Button(self.sidebar, text="Brush", command=self.use_brush, relief="flat", bg="#ecf0f1").pack(fill="x", pady=5)
        tk.Button(self.sidebar, text="Eraser", command=self.use_eraser, relief="flat", bg="#ecf0f1").pack(fill="x", pady=5)
        
        tk.Label(self.sidebar, text="SIZE", fg="white", bg="#34495e", font=("Arial", 8)).pack(pady=(15, 0))
        self.size_slider = tk.Scale(self.sidebar, from_=1, to=50, orient="vertical", bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(fill="y", pady=5)

        tk.Button(self.sidebar, text="Clear", command=self.clear_canvas, bg="#e74c3c", fg="white", relief="flat").pack(side="bottom", fill="x", pady=5)

        # Canvas Area
        self.canvas_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=15)
        self.canvas_frame.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="pencil", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def show_settings_message(self, event):
        # Full screen overlay
        self.overlay = tk.Frame(self.root, bg="#000000", cursor="hand2")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Click anywhere to close
        self.overlay.bind("<Button-1>", lambda e: self.overlay.destroy())

        msg = "This is a free app\nno ads ofc\nno payment needed\nonly you and all users to use it"
        lbl = tk.Label(self.overlay, text=msg, fg="white", bg="black", font=("Arial", 18, "bold"), justify="center")
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        lbl.bind("<Button-1>", lambda e: self.overlay.destroy())

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                remote_version = response.text.strip()
                # Only update if the online version is different from local 1.0.2
                if remote_version != CURRENT_VERSION:
                    if messagebox.askyesno("Update Available", f"Version {remote_version} is ready. Install new update?"):
                        if messagebox.askyesno("Update", "Restart to bring the update to the new version?"):
                            os.execl(sys.executable, sys.executable, *sys.argv)
        except:
            pass

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected
            self.color_preview.configure(bg=selected)

    def use_brush(self):
        self.current_color = self.draw_color
        self.canvas.config(cursor="pencil")

    def use_eraser(self):
        self.current_color = "white"
        self.canvas.config(cursor="dot")

    def clear_canvas(self):
        if messagebox.askyesno("Confirm", "Clear everything?"):
            self.canvas.delete("all")

    def paint(self, event):
        self.brush_size = self.size_slider.get()
        if self.last_x and self.last_y:
            self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=self.brush_size, fill=self.current_color,
                capstyle=tk.ROUND, smooth=tk.TRUE
            )
        self.last_x = event.x
        self.last_y = event.y

    def reset(self, event):
        self.last_x, self.last_y = None, None

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
