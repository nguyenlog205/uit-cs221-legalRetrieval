import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';

// --- Import tất cả các thành phần ---
import Navbar from './components/Navbar/Navbar';
import HomePage from './pages/HomePage/HomePage';
import AboutSection from './components/AboutSection/AboutSection';
import ChatPage from './pages/ChatPage/ChatPage';
import Footer from './components/Footer/Footer';
import ParticleBackground from './components/ParticleBackground/ParticleBackground';

// Import file CSS chính
import './App.css';

// --- Component phụ để nhóm các section của trang chủ ---
const HomeLayout = () => {
  return (
    <>
      <HomePage />
      <AboutSection />
    </>
  );
};


// --- Component App chính ---
function App() {
  // --- Logic quản lý Theme Sáng/Tối ---
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme || 'light';
  });

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);
  // ------------------------------------

  return (
    <div className="app-container">
      {/* Lớp hiệu ứng nền, sẽ nằm sau tất cả nội dung khác */}
      <ParticleBackground />
      
      {/* Navbar luôn hiển thị */}
      <Navbar theme={theme} toggleTheme={toggleTheme} />

      {/* Phần thân chính, nội dung sẽ thay đổi theo trang */}
      <main>
        <Routes>
          <Route path="/" element={<HomeLayout />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>

      {/* Footer luôn hiển thị */}
      <Footer />
    </div>
  );
}

export default App;