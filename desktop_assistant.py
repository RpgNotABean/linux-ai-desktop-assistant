#!/usr/bin/env python3
"""Native Linux desktop assistant with optional local Ollama planning."""
import json
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import URLError
from urllib.request import Request, urlopen
import webbrowser
from urllib.parse import urlsplit

APP_COMMANDS = {
    "firefox": ("firefox",), "chromium": ("chromium", "chromium-browser"),
    "chrome": ("google-chrome", "google-chrome-stable"), "nemo": ("nemo",),
    "xed": ("xed",), "libreoffice": ("libreoffice",), "vlc": ("vlc",),
    "code": ("code",),
}
AI_PROMPT = '''You are a cautious desktop assistant. Convert the user's request into exactly one JSON object and nothing else. Allowed action types are open-app, open-url, and unsupported. For open-app use {"type":"open-app","name":"firefox","description":"Launch Firefox"}; the only allowed names are firefox, chromium, chrome, nemo, xed, libreoffice, vlc, code. For open-url use {"type":"open-url","url":"https://example.com","description":"Open example.com in the default browser"}. For everything else (including clicking, typing, file changes, deleting, system settings, or multiple actions) use {"type":"unsupported","description":"Explain that this action is not available"}. Never claim to have performed an action. The app will ask the user before carrying out any allowed action.'''


def validate_action(action):
    if not isinstance(action, dict):
        raise ValueError("The AI did not return a valid action.")
    kind = action.get("type")
    if kind == "open-app":
        name = action.get("name")
        if not isinstance(name, str) or name.lower() not in APP_COMMANDS:
            return {"type": "unsupported", "description": "That app is not on the safe allowlist."}
        return {"type": "open-app", "name": name.lower(), "description": f"Launch the allowed app: {name.lower()}"}
    if kind == "open-url":
        url = action.get("url")
        if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 32 for c in url):
            raise ValueError("The AI proposed an invalid web address.")
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
            raise ValueError("Only valid http:// and https:// addresses are allowed.")
        return {"type": "open-url", "url": url, "description": f"Open this website in your default browser: {url}"}
    return {"type": "unsupported", "description": str(action.get("description", "This action is outside the safe allowlist."))[:500]}


def ask_ollama(model, prompt):
    payload = {"model": model, "stream": False, "format": "json", "messages": [
        {"role": "system", "content": AI_PROMPT}, {"role": "user", "content": prompt}
    ]}
    request = Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=90) as response:
        result = json.loads(response.read(1024 * 1024))
    return validate_action(json.loads(result["message"]["content"]))


def perform_action(action):
    if action["type"] == "open-app":
        candidates = APP_COMMANDS[action["name"]]
        executable = next((shutil.which(cmd) for cmd in candidates if shutil.which(cmd)), None)
        if not executable:
            raise RuntimeError(f"{action['name']} is not installed or not on PATH.")
        subprocess.Popen([executable], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return f"Launched {action['name']}."
    if action["type"] == "open-url":
        if not webbrowser.open(action["url"], new=2):
            raise RuntimeError("Could not open the default browser.")
        return "Opened the website in your default browser."
    raise ValueError("This action is not allowed.")


class AssistantApp:
    def __init__(self, root):
        self.root = root
        root.title("Linux Desktop Assistant")
        root.geometry("940x690")
        root.minsize(720, 580)
        root.configure(bg="#0b1220")
        self.busy = False
        self.phase = 0
        self._style()
        self._build()
        self._animate()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#111b2c")
        style.configure("TLabel", background="#111b2c", foreground="#eaf2ff", font=(" sans", 11))
        style.configure("Header.TLabel", font=(" sans", 21, "bold"), foreground="#f4f8ff")
        style.configure("Muted.TLabel", foreground="#aab9d1")
        style.configure("TButton", padding=9, font=(" sans", 10, "bold"))

    def _build(self):
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)
        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 14))
        ttk.Label(top, text="Your desktop companion", style="Header.TLabel").pack(side="left")
        self.status = ttk.Label(top, text="Ready", style="Muted.TLabel")
        self.status.pack(side="right")
        content = ttk.Frame(outer)
        content.pack(fill="both", expand=True)
        left = ttk.Frame(content, padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(content, padding=16)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ttk.Label(left, text="Ask the local AI", style="Header.TLabel").pack(anchor="w")
        ttk.Label(left, text="AI plans one safe action; you approve it before it runs.", style="Muted.TLabel", wraplength=390).pack(anchor="w", pady=(5, 14))
        ttk.Label(left, text="Ollama model (installed locally):").pack(anchor="w")
        self.model = tk.StringVar(value="qwen2.5:3b")
        ttk.Entry(left, textvariable=self.model).pack(fill="x", pady=(5, 12))
        ttk.Label(left, text="What would you like done?").pack(anchor="w")
        self.prompt = tk.Text(left, height=5, wrap="word", bg="#080e1b", fg="#f3f6fc", insertbackground="white", relief="flat", padx=10, pady=10)
        self.prompt.pack(fill="x", pady=(5, 10))
        self.ask_button = ttk.Button(left, text="Ask AI to plan", command=self.ask_ai)
        self.ask_button.pack(anchor="e")
        ttk.Label(left, text="Activity", style="Header.TLabel").pack(anchor="w", pady=(22, 8))
        self.log = tk.Listbox(left, height=9, bg="#080e1b", fg="#d7e4f7", relief="flat", selectbackground="#263c5c", activestyle="none")
        self.log.pack(fill="both", expand=True)
        ttk.Label(right, text="Your assistant", style="Header.TLabel").pack(anchor="w")
        self.canvas = tk.Canvas(right, height=310, bg="#142239", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(12, 12))
        self.caption = ttk.Label(right, text="Ready when you are", style="Muted.TLabel", wraplength=400)
        self.caption.pack(anchor="w")
        ttk.Label(right, text="Safety rules", style="Header.TLabel").pack(anchor="w", pady=(20, 6))
        ttk.Label(right, text="• Every desktop action needs your approval.\n• Can only open allowlisted apps and web addresses.\n• Cannot delete files, change settings, type, or click in other apps.\n• AI runs locally through Ollama; requests are not sent to a cloud AI service.", style="Muted.TLabel", wraplength=410, justify="left").pack(anchor="w")
        self.root.bind("<Control-Return>", lambda _event: self.ask_ai())

    def log_line(self, text):
        self.log.insert(0, text)

    def ask_ai(self):
        prompt = self.prompt.get("1.0", "end").strip()
        model = self.model.get().strip()
        if not prompt:
            messagebox.showinfo("Tell me what to do", "Enter a request first.", parent=self.root)
            return
        if not model or len(model) > 100:
            messagebox.showerror("Invalid model", "Enter a valid local Ollama model name.", parent=self.root)
            return
        self.busy = True
        self.ask_button.configure(state="disabled")
        self.status.configure(text="Thinking…")
        self.caption.configure(text="Thinking through your request…")
        self.log_line("Planning: " + prompt[:180])
        threading.Thread(target=self._plan_worker, args=(model, prompt), daemon=True).start()

    def _plan_worker(self, model, prompt):
        try:
            action = ask_ollama(model, prompt)
            self.root.after(0, lambda: self._plan_done(action, None))
        except URLError as error:
            message = "Cannot reach local Ollama. Install/start Ollama and download the selected model."
            if getattr(error, "reason", None):
                message += f" ({error.reason})"
            self.root.after(0, lambda m=message: self._plan_done(None, m))
        except Exception as error:
            self.root.after(0, lambda m=str(error): self._plan_done(None, m))

    def _plan_done(self, action, error):
        self.busy = False
        self.ask_button.configure(state="normal")
        if error:
            self.status.configure(text="Needs setup")
            self.caption.configure(text=error)
            self.log_line("Not run: " + error)
            messagebox.showerror("Local AI unavailable", error + "\n\nOn Linux Mint, install Ollama, then run `ollama pull qwen2.5:3b` in a terminal and try again.", parent=self.root)
            return
        if action["type"] == "unsupported":
            self.status.configure(text="Not available")
            self.caption.configure(text=action["description"])
            self.log_line("Not run: " + action["description"])
            return
        self.status.configure(text="Awaiting approval")
        self.caption.configure(text="Review the exact action in the approval dialog.")
        approved = messagebox.askyesno("Approve this action?", action["description"] + "\n\nOnly approve if this is exactly what you want.", parent=self.root, icon="warning")
        if not approved:
            self.status.configure(text="Denied")
            self.caption.configure(text="No action was taken.")
            self.log_line("Denied: " + action["description"])
            return
        self.status.configure(text="Working…")
        self.caption.configure(text="Working on the approved action…")
        self.log_line("Approved: " + action["description"])
        try:
            result = perform_action(action)
            self.status.configure(text="Done")
            self.caption.configure(text=result)
            self.log_line(result)
        except Exception as error:
            self.status.configure(text="Blocked")
            self.caption.configure(text=str(error))
            self.log_line("Blocked: " + str(error))

    def _animate(self):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 300)
        cx = width // 2
        bob = int(5 * __import__("math").sin(self.phase / 5))
        y = 50 + bob
        self.canvas.create_oval(cx-63, 276, cx+63, 294, fill="#080e1b", outline="")
        self.canvas.create_line(cx, y+5, cx, y+34, fill="#dceaff", width=4)
        self.canvas.create_oval(cx-7, y-3, cx+7, y+11, fill="#55caff", outline="")
        self.canvas.create_rounded_rectangle(cx-43, y+30, cx+43, y+103, radius=24, fill="#dcecff", outline="#30496b", width=3)
        self.canvas.create_oval(cx-23, y+54, cx-11, y+72, fill="#152b48", outline="")
        self.canvas.create_oval(cx+11, y+54, cx+23, y+72, fill="#152b48", outline="")
        self.canvas.create_arc(cx-12, y+68, cx+12, y+86, start=200, extent=140, style="arc", outline="#23466c", width=3)
        self.canvas.create_rounded_rectangle(cx-48, y+100, cx+48, y+170, radius=15, fill="#438fff", outline="#30496b", width=3)
        swing = 15 if self.busy and self.phase % 2 else -8 if self.busy else 0
        self.canvas.create_line(cx-44, y+115, cx-59-swing, y+167, fill="#dcecff", width=13, capstyle="round")
        self.canvas.create_line(cx+44, y+115, cx+59+swing, y+167, fill="#dcecff", width=13, capstyle="round")
        self.canvas.create_line(cx-23, y+165, cx-25, y+220, fill="#dcecff", width=14, capstyle="round")
        self.canvas.create_line(cx+23, y+165, cx+25, y+220, fill="#dcecff", width=14, capstyle="round")
        self.phase += 1
        self.root.after(180, self._animate)


def main():
    root = tk.Tk()
    AssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
