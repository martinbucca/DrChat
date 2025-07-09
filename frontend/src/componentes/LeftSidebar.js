import React from 'react';
import { MessageCircleQuestion, ArrowLeft } from 'lucide-react';

const LeftSidebar = ({ frequentQuestions, handleFrequentQuestionClick, handleBackToWelcome }) => (
  <div className="sidebar left-sidebar">
    <h3><MessageCircleQuestion size={20} /> Preguntas Frecuentes</h3>
    {frequentQuestions.map((q, index) => (
      <div key={index} className="sidebar-item" onClick={() => handleFrequentQuestionClick(q)}>
        {q}
      </div>
    ))}
    <div className="sidebar-footer">
      <button className="back-button" onClick={handleBackToWelcome}>
        <ArrowLeft size={20} /> Volver
      </button>
    </div>
  </div>
);

export default LeftSidebar;
