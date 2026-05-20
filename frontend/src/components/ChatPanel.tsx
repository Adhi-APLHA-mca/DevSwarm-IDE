import "../styles/ChatPanel.css";
import { useState } from "react";

interface ChatPanelProps {
  onSendInitial: (message: string) => void;
  onSendAnswer: (answer: string) => void;
  isSessionActive: boolean;
  isLoading: boolean;
}

export default function ChatPanel({ 
  onSendInitial, 
  onSendAnswer, 
  isSessionActive,
  isLoading 
}: ChatPanelProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim()) {
      if (isSessionActive) {
        onSendAnswer(message);
      } else {
        onSendInitial(message);
      }
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAddFile = () => {
    console.log("Add file clicked");
  };

  const handleVoice = () => {
    console.log("Voice input clicked");
  };

  return (
    <div className="chat-panel">
      <div className="chat-box">
        <button 
          className="icon-btn" 
          onClick={handleAddFile} 
          title="Add file"
          disabled={isLoading}
        >
          +
        </button>

        <input
          type="text"
          placeholder={isSessionActive ? "Answer the question..." : "Describe what to build"}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />

        <button 
          className="icon-btn" 
          onClick={handleVoice} 
          title="Voice input"
          disabled={isLoading}
        >
          🎤
        </button>

        <button 
          className="send-btn" 
          onClick={handleSend} 
          disabled={!message.trim() || isLoading}
        >
          {isLoading ? "..." : "↑"}
        </button>
      </div>
    </div>
  );
}