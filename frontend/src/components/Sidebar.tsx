import { FileText, Search, Zap, GitBranch, Package, Settings } from 'lucide-react';
import '../styles/Sidebar.css';

interface SidebarProps {
  activePanel: string;
  onPanelChange: (panel: string) => void;
}

export default function Sidebar({ activePanel, onPanelChange }: SidebarProps) {
  const panels = [
    { id: 'explorer', icon: FileText, label: 'Explorer', tooltip: 'File Explorer' },
    { id: 'search', icon: Search, label: 'Search', tooltip: 'Search' },
    { id: 'scm', icon: GitBranch, label: 'SCM', tooltip: 'Source Control' },
    { id: 'debug', icon: Zap, label: 'Debug', tooltip: 'Debug' },
    { id: 'extensions', icon: Package, label: 'Extensions', tooltip: 'Extensions' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-icons">
        {panels.map(panel => (
          <button
            key={panel.id}
            className={`sidebar-icon ${activePanel === panel.id ? 'active' : ''}`}
            onClick={() => onPanelChange(panel.id)}
            title={panel.tooltip}
          >
            <panel.icon size={24} />
          </button>
        ))}
      </div>

      <div className="sidebar-bottom">
        <button className="sidebar-icon settings-icon" title="Settings">
          <Settings size={24} />
        </button>
      </div>
    </div>
  );
}
