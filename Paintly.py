import tkinter as tk
from tkinter import messagebox
from tkinter.colorchooser import askcolor
import requests
import sys
import os

# Set your current version
CURRENT_VERSION = "1.0.0"
# URL to a raw text file on GitHub containing the latest version number (e.g., "1.1.0")
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/main/version.txt"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly - v{CURRENT_VERSION}")
        self.root.geometry("900x650")

        self.draw_color = "black"
        self.current_color = "black"
        self.brush_size = 5
        self.last_x, self.last_y = None, None

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        self.controls = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        self.controls.pack(side="top", fill="x")

        tk.Button(self.controls, text="Select Color", command=self.change_color).pack(side="left", padx=5)
        tk.Button(self.controls, text="Brush", command=self.use_brush).pack(side="left", padx=5)
        tk.Button(self.controls, text="Eraser", command=self.use_eraser).pack(side="left", padx=5)

        tk.Label(self.controls, text="Size:", bg="#f0f0f0").pack(side="left", padx=(10, 0))
        self.size_slider = tk.Scale(self.controls, from_=1, to=50, orient="horizontal")
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(side="left", padx=5)

        tk.Button(self.controls, text="Clear All", command=self.clear_canvas).pack(side="right", padx=5)

        self.canvas = tk.Canvas(self.root, bg="white", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            latest_version = response.text.strip()

            if latest_version > CURRENT_VERSION:
                answer = messagebox.askyesno("Update Available", f"Version {latest_version} is available. Install new update?")
                if answer: # User clicked Yes
                    restart = messagebox.askyesno("Update", "Update downloaded. Restart to apply changes?")
                    if restart:
                        # This restarts the current script
                        os.execl(sys.executable, sys.executable, *sys.argv)
                else: # User clicked No
                    pass 
        except Exception:
            # If GitHub is down or no internet, just skip the check
            pass

    def change_color(self):
        selected = askcolor(color=self.draw_color)[1]
        if selected:
            self.draw_color = selected
            self.current_color = selected # Automatically switch to brush mode

    def use_brush(self):
        self.current_color = self.draw_color

    def use_eraser(self):
        self.current_color = "white"

    def clear_canvas(self):
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
