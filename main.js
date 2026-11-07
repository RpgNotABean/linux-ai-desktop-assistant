const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const ALLOWED_APPS = [
  'firefox',
  'google-chrome',
  'chromium',
  'chromium-browser',
  'code',
  'code-insiders',
  'nautilus',
  'thunar',
  'gnome-terminal',
  'konsole',
  'spotify',
  'vlc'
];

const isSafeUrl = (candidate) => {
  if (!candidate) return false;
  try {
    const url = new URL(candidate);
    return ['http:', 'https:'].includes(url.protocol);
  } catch {
    return false;
  }
};

const commandExists = (cmd) => {
  return new Promise((resolve) => {
    const child = spawn('bash', ['-lc', `command -v "${cmd}" >/dev/null 2>&1 && echo yes || echo no`], {
      stdio: ['ignore', 'pipe', 'pipe']
    });

    let stdout = '';
    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.on('close', () => resolve(stdout.trim() === 'yes'));
  });
};

const safeOpenApp = async (appName) => {
  const cleanName = String(appName || '').trim();

  if (!cleanName || !ALLOWED_APPS.includes(cleanName.toLowerCase())) {
    throw new Error(`App "${cleanName}" is not on the approved app list.`);
  }

  const exists = await commandExists(cleanName);
  if (!exists) {
    throw new Error(`App "${cleanName}" was not found on this Linux system.`);
  }

  const child = spawn(cleanName, {
    stdio: 'ignore',
    detached: true
  });

  child.unref();
  return { ok: true, app: cleanName };
};

const safeOpenUrl = async (url) => {
  const cleanUrl = String(url || '').trim();
  if (!isSafeUrl(cleanUrl)) {
    throw new Error('Only http:// and https:// URLs are allowed.');
  }

  await shell.openExternal(cleanUrl);
  return { ok: true, url: cleanUrl };
};

const safeOpenFolder = async (folderPath) => {
  const cleanPath = String(folderPath || '').trim();
  if (!cleanPath) {
    throw new Error('Folder path is required.');
  }

  const result = await shell.openPath(cleanPath);
  if (result && result !== '') {
    throw new Error(result);
  }

  return { ok: true, folder: cleanPath };
};

const createWindow = () => {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 780,
    minWidth: 980,
    minHeight: 700,
    title: 'Linux AI Desktop Assistant',
    backgroundColor: '#0d1220',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.handle('open-app', async (_event, payload) => {
  return safeOpenApp(payload?.name);
});

ipcMain.handle('open-url', async (_event, payload) => {
  return safeOpenUrl(payload?.url);
});

ipcMain.handle('open-folder', async (_event, payload) => {
  return safeOpenFolder(payload?.path);
});
