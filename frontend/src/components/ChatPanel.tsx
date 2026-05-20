import "../styles/ChatPanel.css";
import { useState } from "react";

export default function ChatPanel() {
  const [message, setMessage] = useState("");

  return (
    <div className="chat-panel">
      <div className="chat-box">
        <button className="icon-btn">+</button>

        <input
          type="text"
          placeholder="Describe what to build"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />

        <button className="icon-btn">🎤</button>

        <button className="send-btn">↑</button>
      </div>
    </div>
  );
}