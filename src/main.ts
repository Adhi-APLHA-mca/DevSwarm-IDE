const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;

const isDev = !app.isPackaged;

let mainWindow: any = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, '../public/icon.png'),
  });

  if (isDev) {
    // Development: load from Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load from bundled files
    const indexPath = path.join(__dirname, '../frontend/index.html');
    mainWindow.loadFile(indexPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// File system IPC handlers
ipcMain.handle('dialog:openDirectory', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle('fs:readDirectory', async (_event, dirPath) => {
  try {
    const files = await fs.readdir(dirPath, { withFileTypes: true });
    return files
      .filter(file => !file.name.startsWith('.')) // Hide hidden files
      .map(file => ({
        name: file.name,
        path: path.join(dirPath, file.name),
        isDirectory: file.isDirectory(),
      }));
  } catch (error) {
    console.error('Error reading directory:', error);
    return [];
  }
});

ipcMain.handle('fs:readFile', async (_event, filePath) => {
  try {
    return await fs.readFile(filePath, 'utf-8');
  } catch (error) {
    console.error('Error reading file:', error);
    return '';
  }
});

ipcMain.handle('fs:writeFile', async (_event, filePath, content) => {
  try {
    await fs.writeFile(filePath, content, 'utf-8');
    return { success: true };
  } catch (error) {
    console.error('Error writing file:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
});

// Recursive file tree builder
async function buildFileTree(dirPath, maxDepth = 5, currentDepth = 0) {
  if (currentDepth >= maxDepth) return [];

  try {
    const files = await fs.readdir(dirPath, { withFileTypes: true });
    const items = [];

    for (const file of files) {
      if (file.name.startsWith('.')) continue; // Skip hidden files

      const fullPath = path.join(dirPath, file.name);
      if (file.isDirectory()) {
        items.push({
          name: file.name,
          path: fullPath,
          type: 'folder',
          children: [],
          isDirectory: true,
        });
      } else {
        items.push({
          name: file.name,
          path: fullPath,
          type: 'file',
          isDirectory: false,
        });
      }
    }

    return items.sort((a, b) => {
      if (a.isDirectory === b.isDirectory) {
        return a.name.localeCompare(b.name);
      }
      return a.isDirectory ? -1 : 1;
    });
  } catch (error) {
    console.error('Error building file tree:', error);
    return [];
  }
}

ipcMain.handle('fs:getFileTree', async (_event, dirPath) => {
  return await buildFileTree(dirPath);
});

ipcMain.handle('fs:createFile', async (_event, folderPath, fileName) => {
  try {
    const filePath = path.join(folderPath, fileName);
    
    // Check if file already exists
    try {
      await fs.access(filePath);
      return { success: false, error: 'File already exists' };
    } catch {
      // File doesn't exist, continue
    }
    
    // Create empty file
    await fs.writeFile(filePath, '', 'utf-8');
    return { success: true, path: filePath };
  } catch (error) {
    console.error('Error creating file:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
});

ipcMain.handle('fs:createFolder', async (_event, folderPath, folderName) => {
  try {
    const newFolderPath = path.join(folderPath, folderName);
    
    // Check if folder already exists
    try {
      await fs.access(newFolderPath);
      return { success: false, error: 'Folder already exists' };
    } catch {
      // Folder doesn't exist, continue
    }
    
    // Create folder
    await fs.mkdir(newFolderPath, { recursive: true });
    return { success: true, path: newFolderPath };
  } catch (error) {
    console.error('Error creating folder:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
});

ipcMain.handle('fs:deleteFile', async (_event, filePath) => {
  try {
    await fs.unlink(filePath);
    return { success: true };
  } catch (error) {
    console.error('Error deleting file:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
});

ipcMain.handle('fs:deleteFolder', async (_event, folderPath) => {
  try {
    // Recursively delete folder and contents
    await fs.rm(folderPath, { recursive: true, force: true });
    return { success: true };
  } catch (error) {
    console.error('Error deleting folder:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
});

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Create application menu
const menu = Menu.buildFromTemplate([
  {
    label: 'File',
    submenu: [
      {
        label: 'Exit',
        accelerator: 'CmdOrCtrl+Q',
        click: () => app.quit(),
      },
    ],
  },
  {
    label: 'Edit',
    submenu: [
      { label: 'Undo', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
      { label: 'Redo', accelerator: 'CmdOrCtrl+Y', role: 'redo' },
      { type: 'separator' },
      { label: 'Cut', accelerator: 'CmdOrCtrl+X', role: 'cut' },
      { label: 'Copy', accelerator: 'CmdOrCtrl+C', role: 'copy' },
      { label: 'Paste', accelerator: 'CmdOrCtrl+V', role: 'paste' },
    ],
  },
  {
    label: 'View',
    submenu: [
      { label: 'Reload', accelerator: 'CmdOrCtrl+R', role: 'reload' },
      { label: 'Toggle DevTools', accelerator: 'F12', role: 'toggleDevTools' },
    ],
  },
]);

Menu.setApplicationMenu(menu);
