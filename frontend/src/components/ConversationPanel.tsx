/**
 * Conversation Panel - Displays chat messages and agent responses
 */
import "../styles/ConversationPanel.css";

export interface Message {
  id: string;
  type: "user" | "agent" | "question" | "system" | "greeting";
  content: string;
  timestamp: number;
  agentName?: string;
  agentType?: string;
}

interface ConversationPanelProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function ConversationPanel({
  messages,
  isLoading = false,
}: ConversationPanelProps) {
  return (
    <div className="conversation-panel">
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"></div>
            <h2>DevSwarm Intelligence Platform</h2>
            <p><strong></strong></p>
            <ul style={{ textAlign: 'left', fontSize: '13px', color: '#a0d8ff', lineHeight: '1.6' }}>
            </ul>
            <p className="empty-hint" style={{ marginTop: '12px' }}>Start by describing what you want to build...</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.type}`}>
              {msg.type === "question" && (
                <div className="message-icon">❓</div>
              )}
              {msg.type === "agent" && (
                <div className="message-icon">🤖</div>
              )}
              {msg.type === "greeting" && (
                <div className="message-icon">🚀</div>
              )}
              {msg.type === "user" && (
                <div className="message-icon">👤</div>
              )}
              {msg.type === "system" && (
                <div className="message-icon">⚙️</div>
              )}

              <div className="message-content">
                {msg.agentName && msg.type !== "user" && (
                  <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#5ba3d0', marginBottom: '4px' }}>
                    {msg.agentName}
                  </div>
                )}
                <p>{msg.content}</p>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="message message-system loading">
            <div className="loading-spinner"></div>
            <p>Processing...</p>
          </div>
        )}
      </div>
    </div>
  );
}
