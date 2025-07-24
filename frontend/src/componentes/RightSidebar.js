import React, { useState } from 'react';
import { History, Search as SearchIcon } from 'lucide-react';

/* const RightSidebar = ({ conversationHistory, handleHistoryQuestionClick }) => (
  <div className="sidebar right-sidebar">
    <h3><History size={20} /> Historial de Preguntas</h3>
    {conversationHistory.filter(msg => msg.sender === 'user').map((message, index) => (
      <div key={index} className="sidebar-item" onClick={() => handleHistoryQuestionClick(message)}>
        {message.text}
      </div>
    ))}
  </div>
); */

const RightSidebar = ({ conversationHistory, handleHistoryQuestionClick, handleSearchChatId, chatId}) => {
  const [searchInput, setSearchInput] = useState('');

  const handleSearch = () => {
    if (searchInput.trim() !== '') {
      handleSearchChatId(searchInput);
    }
  };

  return (
    <div className="sidebar right-sidebar">
      <div className="search-container">
        <input
          type="text"
          placeholder="Buscar por Chat ID"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button onClick={handleSearch}>
          <SearchIcon size={16} />
        </button>
      </div>
      
      <h3><History size={20} /> Historial de Preguntas</h3>

      <div className="history-list">
        {conversationHistory.filter(msg => msg.sender === 'user').map((message, index) => (
          <div key={index} className="sidebar-item" onClick={() => handleHistoryQuestionClick(message)}>
            {message.text}
          </div>
        ))}
      </div>
      <div className="chat-id">
        Chat ID: {chatId}
      </div>
    </div>
  );
};

export default RightSidebar;
