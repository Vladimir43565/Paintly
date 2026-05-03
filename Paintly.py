import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import sys

# --- CONFIGURATION ---
# Set this to a lower number like "1.0.0" to FORCE the update pop-up for testing
CURRENT_VERSION = "1.1.1" 
VERSION_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/Vladimir43565/Paintly/refs/heads/main/Paintly.py"

class PaintlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Paintly - v{CURRENT_VERSION}")
        self.root.geometry("400x300")
        
        tk.Label(root, text=f"Current Version: {CURRENT_VERSION}", font=("Arial", 12)).pack(pady=20)
        tk.Button(root, text="Check Manually", command=self.check_for_updates).pack()

        # Run check on startup
        self.root.after(1000, self.check_for_updates)

    def check_for_updates(self):
        try:
            # Added headers to bypass some caching issues
            response = requests.get(VERSION_URL, timeout=5, headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
            
            if response.status_code == 200:
                remote_version = response.text.strip()
                
                # Debug print to console so you can see what the app "sees"
                print(f"Debug: Local={CURRENT_VERSION}, Remote={remote_version}")
                
                if remote_version != CURRENT_VERSION:
                    if messagebox.askyesno("Update Available", f"A new version ({remote_version}) is available! Update now?"):
                        self.perform_update()
                else:
                    print("App is up to date.")
            else:
                print(f"Failed to reach GitHub. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Update error: {e}")

    def perform_update(self):
        try:
            new_code = requests.get(UPDATE_URL).text
            if "import" in new_code: # Basic check to ensure it's python code
                file_path = os.path.abspath(sys.argv[0])
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                messagebox.showinfo("Success", "Update installed! Restarting...")
                os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintlyApp(root)
    root.mainloop()
