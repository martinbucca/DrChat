import React, { useState } from 'react';
import '../estilos/welcome-card.css'; 

const WelcomeScreen = ({ onStart }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [level, setLevel] = useState('');
  const [specialty, setSpecialty] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name && email && level && specialty) {
      onStart({ name, email, level, specialty });
    }
  };

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <h1>¡Bienvenido/a a DrChat!</h1>
        <p className="subtitle">El asistente virtual para el personal o estudiantes de salud</p>
        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="Nombre Completo" value={name} onChange={(e) => setName(e.target.value)} required />
          <input type="email" placeholder="Email de contacto" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <select value={level} onChange={(e) => setLevel(e.target.value)} required>
            <option value="">Seleccioná tu nivel profesional</option>
            <option value="profesional">Profesional de la salud</option>
            <option value="estudiante">Estudiante</option>
          </select>
          <select value={specialty} onChange={(e) => setSpecialty(e.target.value)} required>
            <option value="">Seleccioná tu especialidad</option>
            <option value="medicina">Medicina</option>
            <option value="enfermeria">Enfermería</option>
            <option value="psicologia">Psicología</option>
            <option value="kinesiologia">Kinesiología</option>
            <option value="nutricion">Nutrición</option>
            <option value="otra">Otra</option>
          </select>
          <button type="submit">Comenzar</button>
        </form>
      </div>
    </div>
  );
};

export default WelcomeScreen;
