import React, { useState } from 'react';
import axios from 'axios';
import { Download, MessageCircleQuestion, History, ArrowLeft, Trash } from 'lucide-react';

const WelcomeScreen = ({ onStart }) => {
  const [name, setName] = useState('');
  const [year, setYear] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name && year) {
      onStart({ name, year });
    }
  };

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <h1>Bienvenido al Chatbot de FIUBA</h1>
        <form onSubmit={handleSubmit}>
          <input 
            type="text" 
            placeholder="Nombre Completo" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            required 
          />
          <select 
            value={year} 
            onChange={(e) => setYear(e.target.value)}
            required
          >
            <option value="">Selecciona tu año de cursada</option>
            <option value="1">1er Año</option>
            <option value="2">2do Año</option>
            <option value="3">3er Año</option>
            <option value="4">4to Año</option>
            <option value="5">5to Año</option>
          </select>
          <button type="submit">Comenzar</button>
        </form>
      </div>
    </div>
  );
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [frequentQuestions, setFrequentQuestions] = useState([
    '¿Cuáles son los horarios de la biblioteca?',
    '¿Cómo inscribirse a materias?',
    '¿Dónde puedo ver mi historial académico?',
    'Requisitos para cambiar de plan de estudio'
  ]);
  const [conversationHistory, setConversationHistory] = useState([]);

  const getSuggestedQuestions = (year) => {
    const yearQuestions = {
      '1': [
        '¿Cómo funciona el CBC?',
        'Materias recomendadas para primer año',
        'Información sobre inscripciones'
      ],
      '2': [
        'Materias de segundo año',
        'Cambio de plan de estudio',
        'Requisitos para seguir avanzando'
      ],
      '3': [
        'Materias optativas',
        'Prácticas profesionales',
        'Proyectos de investigación'
      ],
      '4': [
        'Preparación para el trabajo final',
        'Salidas laborales',
        'Materias de especialización'
      ],
      '5': [
        'Trámites de graduación',
        'Últimos pasos para recibirse',
        'Oportunidades de posgrado'
      ]
    };
    return yearQuestions[year] || [];
  };

  const handleSendMessage = async () => {
    if (userInput.trim() === '') return;

    const userMessage = { sender: 'user', text: userInput };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    
    setConversationHistory([...conversationHistory, userMessage]);
    
    setUserInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/find_chunk', {
        query: userInput,
      });
      const botMessage = { sender: 'bot', text: response.data.answer };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
      
      setConversationHistory((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: 'Hubo un error al procesar tu solicitud.' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = () => {
    const reportContent = messages.map(msg => 
      `${msg.sender.toUpperCase()}: ${msg.text}`
    ).join('\n');

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chatbot_conversation_${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
  };

  const handleStartChat = (userData) => {
    setUser(userData);
    setShowWelcome(false);
    setFrequentQuestions(getSuggestedQuestions(userData.year));
  };

  const handleFrequentQuestionClick = (question) => {
    setUserInput(question);
    handleSendMessage();
  };

  const handleHistoryQuestionClick = (message) => {
    setUserInput(message.text);
    handleSendMessage();
  };

  const handleBackToWelcome = () => {
    setUser(null);
    setShowWelcome(true);
  };

  const getYearSuffix = (year) => {
    switch (year) {
      case '1':
        return 'ro';
      case '2':
        return 'do';
      case '3':
        return 'ro';
      case '4':
        return 'to';
      case '5':
        return 'to';
      default:
        return '';
    }
  };

  const handleClearChat = () => {
    setUserInput('');
  };

  if (showWelcome) {
    return <WelcomeScreen onStart={handleStartChat} />;
  }

  return (
    <div className="app-container">
      <div className="sidebar left-sidebar">
        <h3><MessageCircleQuestion size={20} /> Preguntas Frecuentes</h3>
        {frequentQuestions.map((q, index) => (
          <div
            key={index}
            className="sidebar-item"
            onClick={() => handleFrequentQuestionClick(q)}
          >
            {q}
          </div>
        ))}
        <div className="sidebar-footer">
          <button className="back-button" onClick={handleBackToWelcome}>
            <ArrowLeft size={20} /> Volver
          </button>
        </div>
      </div>

      <div className="chatbot-container">
        <div className="chatbot-header">
          <img src="/fiuba.png" alt="FIUBA Logo" className="fiuba-logo" />
          <h1 className="chatbot-title">FIUBA Chatbot</h1>
          <div className="welcome-user">
            ¡Bienvenido/a, {user.name}! (Año: {user.year}{getYearSuffix(user.year)})
          </div>
          <button 
            className="download-report" 
            onClick={handleDownloadReport}
          >
            <Download size={20} /> Descargar Reporte
          </button>
        </div>
        
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
        
        <div className="input-container">
          <textarea
            placeholder="Escribe tu pregunta..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            rows={3}
          />
          <button onClick={handleSendMessage}>Enviar</button>
          <button 
            className="clear-chat-button" 
            onClick={handleClearChat}
          >
            <Trash size={20} /> Limpiar
          </button>
        </div>
      </div>

      <div className="sidebar right-sidebar">
        <h3><History size={20} /> Historial de Preguntas</h3>
        {conversationHistory
          .filter(msg => msg.sender === 'user')
          .map((message, index) => (
            <div 
              key={index} 
              className="sidebar-item"
              onClick={() => handleHistoryQuestionClick(message)}
            >
              {message.text}
            </div>
          ))
        }
      </div>
    </div>
  );
};

export default App;