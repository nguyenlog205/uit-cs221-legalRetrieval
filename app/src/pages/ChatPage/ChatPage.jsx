import React, { useState, useRef, useEffect } from 'react';
import './ChatPage.css';

const SendIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" /></svg>
);

const ChatPage = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Xin chào! Tôi có thể giúp gì cho bạn về các vấn đề pháp lý y tế?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() === '' || isLoading) return;
    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // TODO: Replace with real API call
    setTimeout(() => {
      const botResponse = { sender: 'bot', text: `Bot đang xử lý...` };
      setMessages(prev => [...prev, botResponse]);
      setIsLoading(false);
    }, 1500);
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-page-container">
      <div className="chat-box">
        <div className="vietnam-pattern"></div>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message-bubble ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          {isLoading && (
            <div className="message-bubble bot typing-indicator">
              <span></span><span></span><span></span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi của bạn (Shift + Enter để xuống dòng)..."
            disabled={isLoading}
            rows={1}
          />
          <button onClick={handleSend} disabled={isLoading || input.trim() === ''}>
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;