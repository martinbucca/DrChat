import { Download, Upload } from 'lucide-react';
import { useRef } from 'react';

const ChatHeader = ({ user, handleDownloadReport }) => {
  const fileInputRef = useRef();

  const handleUploadClick = () => {
    fileInputRef.current.click(); // Abre el diálogo
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        alert('Archivo subido con éxito ✅');
      } else {
        alert('Error al subir archivo ❌');
      }
    } catch (err) {
      console.error(err);
      alert('Error de red o servidor ❌');
    }
  };

  return (
    <div className="chatbot-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <img src="/dr_chat_logo.png" alt="DrChat Logo" className="drchat-logo" />
        <h1 className="chatbot-title">DrChat</h1>
      </div>

      <div className="welcome-user">
        ¡Bienvenido/a, {user.name}!
      </div>

      {/* Botones alineados */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <button className="upload-report" onClick={handleUploadClick}>
          <Upload size={20} /> Cargar archivo
        </button>

        <button className="download-report" onClick={handleDownloadReport}>
          <Download size={20} /> Descargar Reporte
        </button>
      </div>
    </div>
  );
};

export default ChatHeader;

