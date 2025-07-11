
const InputBox = ({ userInput, setUserInput, handleSendMessage, handleClearChat }) => (
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
    <button className="send-button" onClick={handleSendMessage}>
      Enviar</button>
      
    <button className="clear-chat-button" onClick={handleClearChat}>
    Limpiar
    </button>
  </div>
);

export default InputBox;
