#!/usr/bin/env python3
"""Lightweight Linux desktop assistant. Uses only Python's standard library."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json
import secrets
import shutil
import subprocess
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
APP_COMMANDS = {
    "firefox": ("firefox",),
    "chromium": ("chromium", "chromium-browser"),
    "chrome": ("google-chrome", "google-chrome-stable"),
    "nemo": ("nemo",),
    "xed": ("xed",),
    "libreoffice": ("libreoffice",),
    "vlc": ("vlc",),
    "code": ("code",),
}
MIME_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}


def execute_action(action):
    kind = action.get("type")
    if kind == "open-url":
        url = action.get("url", "")
        parts = urlsplit(url)
        if (len(url) > 2048 or any(ord(char) < 32 for char in url)
                or parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username or parts.password):
            raise ValueError("Enter a valid http:// or https:// web address.")
        if not webbrowser.open(url, new=2):
            raise RuntimeError("Could not open the default browser.")
        return "Opened the website in your default browser."

    if kind == "open-app":
        name = action.get("name", "").strip().lower()
        candidates = APP_COMMANDS.get(name)
        if not candidates:
            raise ValueError("That app is not on the allowed app list.")
        executable = next((shutil.which(candidate) for candidate in candidates if shutil.which(candidate)), None)
        if not executable:
            raise RuntimeError(f"{name} does not appear to be installed.")
        subprocess.Popen([executable], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return f"Launched {name}."

    raise ValueError("That action is not allowed.")


class Handler(BaseHTTPRequestHandler):
    server_version = "SafeAssistant/1.0"

    def send_bytes(self, status, content, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        paths = {"/": WEB_ROOT / "index.html", "/styles.css": WEB_ROOT / "styles.css", "/app.js": WEB_ROOT / "app.js"}
        file_path = paths.get(self.path)
        if not file_path:
            self.send_error(404)
            return
        content = file_path.read_bytes()
        if self.path == "/":
            content = content.replace(b"__SESSION_TOKEN__", self.server.session_token.encode("ascii"))
        self.send_bytes(200, content, MIME_TYPES[file_path.suffix])

    def do_POST(self):
        if self.path != "/api/execute":
            self.send_error(404)
            return
        if self.headers.get("X-Assistant-Token") != self.server.session_token:
            self.send_error(403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("Invalid request size.")
            action = json.loads(self.rfile.read(length))
            if not isinstance(action, dict):
                raise ValueError("Invalid action request.")
            message = execute_action(action)
            response = {"ok": True, "message": message}
            status = 200
        except (ValueError, json.JSONDecodeError, RuntimeError) as error:
            response = {"ok": False, "message": str(error)}
            status = 400
        except Exception:
            response = {"ok": False, "message": "The action could not be completed."}
            status = 500
        self.send_bytes(status, json.dumps(response).encode("utf-8"), "application/json; charset=utf-8")

    def log_message(self, _format, *_args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.session_token = secrets.token_urlsafe(32)
    address, port = server.server_address
    url = f"http://{address}:{port}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Assistant running at {url}\nClose this terminal or press Ctrl+C to quit.")
    webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down assistant.")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
