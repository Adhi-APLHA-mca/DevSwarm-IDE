const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAppName: () => 'DevSwarm',
  getAppVersion: () => '0.1.0',
  
  // File system APIs
  openFolder: () => ipcRenderer.invoke('dialog:openDirectory'),
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  readDirectory: (dirPath: string) => ipcRenderer.invoke('fs:readDirectory', dirPath),
  readFile: (filePath: string) => ipcRenderer.invoke('fs:readFile', filePath),
  writeFile: (filePath: string, content: string) => ipcRenderer.invoke('fs:writeFile', filePath, content),
  getFileTree: (dirPath: string) => ipcRenderer.invoke('fs:getFileTree', dirPath),
  createFile: (folderPath: string, fileName: string) => ipcRenderer.invoke('fs:createFile', folderPath, fileName),
  createFolder: (folderPath: string, folderName: string) => ipcRenderer.invoke('fs:createFolder', folderPath, folderName),
  deleteFile: (filePath: string) => ipcRenderer.invoke('fs:deleteFile', filePath),
  deleteFolder: (folderPath: string) => ipcRenderer.invoke('fs:deleteFolder', folderPath),
});
