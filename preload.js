const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openApp: (name) => ipcRenderer.invoke('open-app', { name }),
  openUrl: (url) => ipcRenderer.invoke('open-url', { url }),
  openFolder: (path) => ipcRenderer.invoke('open-folder', { path })
});
