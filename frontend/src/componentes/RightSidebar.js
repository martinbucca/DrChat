import React from 'react';
import { History } from 'lucide-react';

const RightSidebar = ({ conversationHistory, handleHistoryQuestionClick }) => (
  <div className="sidebar right-sidebar">
    <h3><History size={20} /> Historial de Preguntas</h3>
    {conversationHistory.filter(msg => msg.sender === 'user').map((message, index) => (
      <div key={index} className="sidebar-item" onClick={() => handleHistoryQuestionClick(message)}>
        {message.text}
      </div>
    ))}
  </div>
);

export default RightSidebar;
