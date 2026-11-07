# Linux AI Desktop Assistant

A native-window desktop assistant prototype for Linux Mint. The UI is a real Tk desktop window (not a browser tab or Electron app); Python's standard library is used for the app. A local Ollama model provides natural-language planning. The model can only propose opening one allowlisted app or an HTTP/HTTPS website, and the app asks you before carrying it out.

## Run the native desktop app

```bash
python3 desktop_assistant.py
```

If Python reports `No module named tkinter`, install the Mint package once with `sudo apt install python3-tk`, then run the command again.

## Enable the local AI

Install Ollama for Linux from its official instructions, start its local service, and download a model once:

```bash
ollama pull qwen2.5:3b
```

Then use the app's default model name `qwen2.5:3b`. The AI talks only to Ollama on `127.0.0.1`; it does not send prompts to a cloud AI provider. The model must be downloaded locally, so the first setup requires an internet connection and disk space.

## Supported actions and limits

- Launch an installed app from a fixed allowlist: Firefox, Chromium, Chrome, Nemo, Xed, LibreOffice, VLC, or Code.
- Open an HTTP/HTTPS website in your default browser.
- The local model can translate natural language into a proposal, but it does not execute actions.
- Every proposed desktop action is shown in a confirmation dialog. Denying means no action is run.
- No deleting files, changing system settings, shell commands, typing/clicking in other apps, or general-purpose computer control.

The original `assistant.py` browser prototype remains available, but `desktop_assistant.py` is the native desktop app. The older Electron files are not needed to run it.
