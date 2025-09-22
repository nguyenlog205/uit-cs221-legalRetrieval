import React from 'react';
import './HomePage.css'; // Dòng này sẽ tìm và nạp file CSS ở dưới

const HomePage = () => {
  return (
    <section className="homepage-section"> 
      <div className="homepage-content">
        <p className="eyebrow-text">TRỢ LÝ PHÁP LÝ AI DÀNH CHO NGƯỜI VIỆT</p>
        <h1>LegalTalk xin chào!</h1>
        <p className="description">
          Nền tảng ứng dụng chuyên biệt hỗ trợ người Việt Nam tiếp cận các vấn đề
          thủ tục hành chính và pháp lý trong lĩnh vực y tế công cộng.
        </p>
        <button className="cta-button">
          <span>Bắt đầu trò chuyện</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </section>
  );
};

export default HomePage;