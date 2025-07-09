import React from 'react';
import { Download, ArrowLeft } from 'lucide-react';

const ChatHeader = ({ user, handleDownloadReport, handleBackToWelcome, getYearSuffix }) => (
  <div className="chatbot-header">
    <img src="/fiuba.png" alt="FIUBA Logo" className="fiuba-logo" />
    <h1 className="chatbot-title">FIUBA Chatbot</h1>
    <div className="welcome-user">
      ¡Bienvenido/a, {user.name}! (Año: {user.year}{getYearSuffix(user.year)})
    </div>
    <button className="download-report" onClick={handleDownloadReport}>
      <Download size={20} /> Descargar Reporte
    </button>
  </div>
);

export default ChatHeader;
