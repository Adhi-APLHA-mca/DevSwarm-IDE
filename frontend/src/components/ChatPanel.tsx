import '../styles/ChatPanel.css';

export default function ChatPanel() {
  return (
    <div className="panel-content chat-panel">
      <div className="chat-placeholder">
        <h3>Chat Interface</h3>
        <p>Backend integration coming soon!</p>
        <p className="chat-info">
          This panel will connect to the Python backend via WebSocket/HTTP for
          AI-powered code assistance and workflow management.
        </p>
      </div>
    </div>
  );
}
