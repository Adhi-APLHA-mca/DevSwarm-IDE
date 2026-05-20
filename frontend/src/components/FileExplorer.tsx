import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, File, Folder, Plus, FolderOpen, FilePlus, FolderPlus } from 'lucide-react';
import InputDialog from './InputDialog';
import '../styles/FileExplorer.css';

interface FileExplorerProps {
  onFileSelect: (filePath: string, content: string) => void;
}

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  isDirectory?: boolean;
}

declare global {
  interface Window {
    electronAPI: {
      openFolder: () => Promise<string | null>;
      openFile: () => Promise<string | null>;
      getFileTree: (dirPath: string) => Promise<FileNode[]>;
      readFile: (filePath: string) => Promise<string>;
      writeFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>;
      createFile: (folderPath: string, fileName: string) => Promise<{ success: boolean; path?: string; error?: string }>;
      createFolder: (folderPath: string, folderName: string) => Promise<{ success: boolean; path?: string; error?: string }>;
      deleteFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
      deleteFolder: (folderPath: string) => Promise<{ success: boolean; error?: string }>;
    };
  }
}

export default function FileExplorer({ onFileSelect }: FileExplorerProps) {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [rootPath, setRootPath] = useState<string | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [hoveredPath, setHoveredPath] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  
  // Input dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'file' | 'folder'>('file');
  const [dialogFolderPath, setDialogFolderPath] = useState<string>('');

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Delete' && selectedPath) {
        e.preventDefault();
        handleDelete(selectedPath);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [selectedPath]);

  const openFolder = async () => {
    setLoading(true);
    try {
      const folderPath = await window.electronAPI.openFolder();
      if (folderPath) {
        setRootPath(folderPath);
        const tree = await window.electronAPI.getFileTree(folderPath);
        setFiles(tree);
        setExpandedFolders(new Set());
      }
    } catch (error) {
      console.error('Error opening folder:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFolder = async (nodePath: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(nodePath)) {
      newExpanded.delete(nodePath);
    } else {
      newExpanded.add(nodePath);
      // Load children if not already loaded
      await loadFolderContents(nodePath);
    }
    setExpandedFolders(newExpanded);
  };

  const loadFolderContents = async (folderPath: string) => {
    try {
      console.log('Loading folder contents for:', folderPath);
      const children = await window.electronAPI.getFileTree(folderPath);
      console.log('Loaded children:', children);
      
      // Create a completely new files array to trigger re-render
      const updateTree = (nodes: FileNode[]): FileNode[] => {
        return nodes.map(node => {
          if (node.path === folderPath) {
            return { ...node, children: children };
          }
          if (node.children) {
            return { ...node, children: updateTree(node.children) };
          }
          return node;
        });
      };
      
      const newFiles = updateTree(files);
      console.log('Updated files state');
      setFiles(newFiles);
    } catch (error) {
      console.error('Error loading folder contents:', error);
    }
  };

  const handleFileClick = async (node: FileNode) => {
    if (node.type === 'file') {
      try {
        const content = await window.electronAPI.readFile(node.path);
        onFileSelect(node.path, content);
      } catch (error) {
        console.error('Error reading file:', error);
      }
    }
  };

  const handleCreateFile = async (folderPath: string) => {
    console.log('handleCreateFile called with:', folderPath);
    setDialogType('file');
    setDialogFolderPath(folderPath);
    setDialogOpen(true);
  };

  const handleCreateFolder = async (folderPath: string) => {
    console.log('handleCreateFolder called with:', folderPath);
    setDialogType('folder');
    setDialogFolderPath(folderPath);
    setDialogOpen(true);
  };

  const handleDialogConfirm = async (name: string) => {
    setDialogOpen(false);
    try {
      if (dialogType === 'file') {
        console.log('Creating file:', name, 'in', dialogFolderPath);
        const result = await window.electronAPI.createFile(dialogFolderPath, name);
        console.log('Create file result:', result);
        if (result.success) {
          await loadFolderContents(dialogFolderPath);
          setExpandedFolders(new Set([...expandedFolders, dialogFolderPath]));
        } else {
          alert(`Error creating file: ${result.error}`);
        }
      } else {
        console.log('Creating folder:', name, 'in', dialogFolderPath);
        const result = await window.electronAPI.createFolder(dialogFolderPath, name);
        console.log('Create folder result:', result);
        if (result.success) {
          await loadFolderContents(dialogFolderPath);
          setExpandedFolders(new Set([...expandedFolders, dialogFolderPath]));
        } else {
          alert(`Error creating folder: ${result.error}`);
        }
      }
    } catch (error) {
      console.error('Error creating item:', error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      alert(`Error: ${errorMsg}`);
    }
  };

  const handleDialogCancel = () => {
    setDialogOpen(false);
  };

  const handleDelete = async (itemPath: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete this item? This action cannot be undone.`
    );
    
    if (!confirmed) return;

    try {
      // Find the node to determine if it's a file or folder
      let isFolder = false;
      const findNode = (nodes: FileNode[]): FileNode | null => {
        for (const node of nodes) {
          if (node.path === itemPath) return node;
          if (node.children) {
            const found = findNode(node.children);
            if (found) return found;
          }
        }
        return null;
      };

      const node = findNode(files);
      if (!node) return;

      isFolder = node.type === 'folder';
      console.log(`Deleting ${isFolder ? 'folder' : 'file'}:`, itemPath);

      const result = isFolder
        ? await window.electronAPI.deleteFolder(itemPath)
        : await window.electronAPI.deleteFile(itemPath);

      if (result.success) {
        // Remove from selected
        setSelectedPath(null);
        
        // Find parent folder and refresh it
        const parentPath = itemPath.substring(0, itemPath.lastIndexOf('\\'));
        if (parentPath && parentPath !== rootPath) {
          await loadFolderContents(parentPath);
        } else if (parentPath === rootPath) {
          // Refresh root
          const tree = await window.electronAPI.getFileTree(rootPath);
          setFiles(tree);
        }
      } else {
        alert(`Error deleting item: ${result.error}`);
      }
    } catch (error) {
      console.error('Error deleting item:', error);
      alert('Error deleting item');
    }
  };

  const renderNode = (node: FileNode, level: number = 0) => {
    const isExpanded = expandedFolders.has(node.path);

    return (
      <div key={node.path}>
        <div
          className={`file-item ${selectedPath === node.path ? 'selected' : ''}`}
          style={{ paddingLeft: `${level * 16}px` }}
          onMouseEnter={() => setHoveredPath(node.path)}
          onMouseLeave={() => setHoveredPath(null)}
          onClick={() => {
            setSelectedPath(node.path);
            if (node.type === 'folder') {
              toggleFolder(node.path);
            } else {
              handleFileClick(node);
            }
          }}
        >
          {node.type === 'folder' ? (
            <>
              {isExpanded ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
              <Folder size={16} className="icon-folder" />
              <span>{node.name}</span>
            </>
          ) : (
            <>
              <div className="chevron-spacer" />
              <File size={16} className="icon-file" />
              <span>{node.name}</span>
            </>
          )}
          {hoveredPath === node.path && node.type === 'folder' && (
            <div className="file-item-actions">
              <button
                className="action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCreateFile(node.path);
                }}
                title="Create file"
              >
                <FilePlus size={14} />
              </button>
              <button
                className="action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCreateFolder(node.path);
                }}
                title="Create folder"
              >
                <FolderPlus size={14} />
              </button>
            </div>
          )}
        </div>
        {node.type === 'folder' && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="panel-content file-explorer">
      {!rootPath ? (
        <div className="explorer-empty">
          <Folder size={48} />
          <h3>No Folder Open</h3>
          <button
            className="open-folder-btn"
            onClick={openFolder}
            disabled={loading}
          >
            <FolderOpen size={18} />
            {loading ? 'Opening...' : 'Open Folder'}
          </button>
        </div>
      ) : (
        <>
          <div className="explorer-header">
            <button
              className="open-folder-btn-small"
              onClick={openFolder}
              title="Open another folder"
              disabled={loading}
            >
              <Plus size={14} />
            </button>
            <span className="folder-name" title={rootPath}>
              {rootPath.split('\\').pop()}
            </span>
          </div>
          <div className="explorer-tree">
            {files.length > 0 ? (
              files.map(file => renderNode(file))
            ) : (
              <div className="empty-folder">
                <p>Folder is empty</p>
              </div>
            )}
          </div>
        </>
      )}
      
      <InputDialog
        isOpen={dialogOpen}
        title={dialogType === 'file' ? 'Create New File' : 'Create New Folder'}
        placeholder={dialogType === 'file' ? 'filename.txt' : 'folder-name'}
        onConfirm={handleDialogConfirm}
        onCancel={handleDialogCancel}
      />
    </div>
  );
}
