import React, { useState } from 'react';
import axios from 'axios';
import WelcomeScreen from './componentes/WelcomeScreen';
import ChatHeader from './componentes/ChatHeader';
import ChatWindow from './componentes/ChatWindow';
import InputBox from './componentes/InputBox';
import LeftSidebar from './componentes/LeftSidebar';
import RightSidebar from './componentes/RightSidebar';

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
      '1': ['¿Cómo funciona el CBC?', 'Materias recomendadas para primer año', 'Información sobre inscripciones'],
      '2': ['Materias de segundo año', 'Cambio de plan de estudio', 'Requisitos para seguir avanzando'],
      '3': ['Materias optativas', 'Prácticas profesionales', 'Proyectos de investigación'],
      '4': ['Preparación para el trabajo final', 'Salidas laborales', 'Materias de especialización'],
      '5': ['Trámites de graduación', 'Últimos pasos para recibirse', 'Oportunidades de posgrado']
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
      const response = await axios.post('http://127.0.0.1:5000/find_chunk', { query: userInput });
      const botMessage = { sender: 'bot', text: response.data.answer };
      setMessages(prev => [...prev, botMessage]);
      setConversationHistory(prev => [...prev, botMessage]);
    } catch {
      const errorMessage = { sender: 'bot', text: 'Hubo un error al procesar tu solicitud.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = () => {
    const report = messages.map(msg => `${msg.sender.toUpperCase()}: ${msg.text}`).join('\n');
    const blob = new Blob([report], { type: 'text/plain' });
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

  const handleFrequentQuestionClick = (q) => {
    setUserInput(q);
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
      case '1': return 'ro';
      case '2': return 'do';
      case '3': return 'ro';
      case '4': return 'to';
      case '5': return 'to';
      default: return '';
    }
  };

  const handleClearChat = () => setUserInput('');

  if (showWelcome) return <WelcomeScreen onStart={handleStartChat} />;

  return (
    <div className="app-container">
      <LeftSidebar
        frequentQuestions={frequentQuestions}
        handleFrequentQuestionClick={handleFrequentQuestionClick}
        handleBackToWelcome={handleBackToWelcome}
      />
      <div className="chatbot-container">
        <ChatHeader
          user={user}
          handleDownloadReport={handleDownloadReport}
          getYearSuffix={getYearSuffix}
        />
        <ChatWindow messages={messages} loading={loading} />
        <InputBox
          userInput={userInput}
          setUserInput={setUserInput}
          handleSendMessage={handleSendMessage}
          handleClearChat={handleClearChat}
        />
      </div>
      <RightSidebar
        conversationHistory={conversationHistory}
        handleHistoryQuestionClick={handleHistoryQuestionClick}
      />
    </div>
  );
};

export default App;

