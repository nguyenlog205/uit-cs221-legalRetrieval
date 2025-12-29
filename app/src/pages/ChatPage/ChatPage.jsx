import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown'; // <--- Import thư viện Markdown
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

  // --- 1. LẤY API URL TỪ BIẾN MÔI TRƯỜNG ---
  const API_URL = import.meta.env.VITE_API_URL;

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

  const handleSend = async () => {
    if (input.trim() === '' || isLoading) return;

    // Hiển thị tin nhắn User
    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    
    const queryText = input;
    setInput('');
    setIsLoading(true);

    try {
      // Gọi API Backend
      const targetUrl = API_URL || "http://localhost:8000"; 
      
      const response = await fetch(`${targetUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            query: queryText,
            session_id: "user-default" 
        })
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      // Hiển thị câu trả lời từ Bot
      const botResponse = { sender: 'bot', text: data.response };
      setMessages(prev => [...prev, botResponse]);

    } catch (error) {
      console.error("Lỗi gọi API:", error);
      const errorResponse = { 
        sender: 'bot', 
        text: 'Xin lỗi, server đang bận hoặc gặp sự cố kết nối. Vui lòng thử lại sau.' 
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
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
              {/* --- Thay đổi quan trọng ở đây --- */}
              {/* Sử dụng ReactMarkdown để render text thay vì hiển thị trực tiếp */}
              <div className="markdown-content">
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
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