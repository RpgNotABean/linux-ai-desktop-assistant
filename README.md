# Linux AI Desktop Assistant

A small Linux Mint-friendly desktop assistant prototype. This version uses Python's standard library instead of Electron, Node.js, npm, or downloaded runtime binaries. It opens a local control page in your default browser and includes an animated character.

## Run on Linux Mint

Python 3 is normally available by default. From the project folder run:

```bash
python3 assistant.py
```

The app opens its control page in your default browser. Keep the terminal open while using it; press `Ctrl+C` there to stop the assistant. No npm install is needed.

## Supported actions

- Open a website in your default browser using an `http://` or `https://` URL.
- Launch an app from the built-in allowlist: Firefox, Chromium, Chrome, Nemo, Xed, LibreOffice, VLC, or Code. The chosen app must already be installed.

Each supported action shows a confirmation dialog before it is sent to the local assistant. Denying a request does nothing. The assistant does not delete files, modify system settings, run shell commands, or type/click inside other applications. It is a safe desktop-task prototype, not yet connected to an AI model.

## Safety and implementation

- The local HTTP service listens only on `127.0.0.1` and uses a random per-run token for action requests.
- App launches use fixed executable allowlists and do not invoke a shell.
- Website addresses are limited to HTTP and HTTPS.
- Review every action description before approving it.

The earlier Electron files are retained in the repository, but you do not need Electron, Node.js, or npm to run this Python version.
