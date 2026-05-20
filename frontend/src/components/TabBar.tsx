import { X } from 'lucide-react';
import '../styles/TabBar.css';

interface Tab {
  id: string;
  path: string;
  name: string;
  isDirty: boolean;
}

interface TabBarProps {
  tabs: Tab[];
  activeTabId: string | null;
  onTabClick: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onSaveTab: (tabId: string) => void;
}

export default function TabBar({
  tabs,
  activeTabId,
  onTabClick,
  onTabClose,
  onSaveTab,
}: TabBarProps) {
  return (
    <div className="tab-bar">
      {tabs.length === 0 ? (
        <div className="tab-bar-empty">No files open</div>
      ) : (
        tabs.map(tab => (
          <div
            key={tab.id}
            className={`tab ${activeTabId === tab.id ? 'active' : ''}`}
            onClick={() => onTabClick(tab.id)}
          >
            <span className="tab-label">
              {tab.isDirty && <span className="tab-dirty-indicator">●</span>}
              {tab.name}
            </span>
            <button
              className="tab-close"
              onClick={e => {
                e.stopPropagation();
                if (tab.isDirty) {
                  onSaveTab(tab.id);
                }
                onTabClose(tab.id);
              }}
              title={tab.isDirty ? 'Save and close' : 'Close'}
            >
              <X size={16} />
            </button>
          </div>
        ))
      )}
    </div>
  );
}
