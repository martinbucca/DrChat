import React from 'react';

const ChatWindow = ({ messages, loading }) => (
  <div className="chat-window">
    {messages.map((message, index) => (
      <div key={index} className={`message ${message.sender}`}>
        {message.text}
      </div>
    ))}
    {loading && (
      <div className="message bot">
        Pensando... <span className="spinner"></span>
      </div>
    )}
  </div>
);

export default ChatWindow;
