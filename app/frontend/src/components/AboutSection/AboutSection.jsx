import React, { useRef, useEffect, useState } from 'react';
import './AboutSection.css';

// Custom hook để theo dõi xem element có trong màn hình không
const useOnScreen = (options) => {
  const ref = useRef();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.unobserve(entry.target);
      }
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [ref, options]);

  return [ref, isVisible];
};


const AboutSection = () => {
  const [ref, isVisible] = useOnScreen({ threshold: 0.2 });

  return (
    <section 
      ref={ref} 
      className={`about-section ${isVisible ? 'is-visible' : ''}`}
    >
      <div className="about-container">
        <h2>Về LegalTalk</h2>
        <p className="about-subtitle">
          Một trợ lý ảo thông minh, giúp bạn giải đáp các thắc mắc pháp lý
          trong lĩnh vực y tế một cách nhanh chóng và tin cậy.
        </p>
        <div className="features-grid">
          <div className="feature-card">
            <h3>Nhanh chóng</h3>
            <p>Nhận câu trả lời ngay lập tức, không cần chờ đợi.</p>
          </div>
          <div className="feature-card">
            <h3>Chính xác</h3>
            <p>Dữ liệu được huấn luyện từ các nguồn văn bản pháp luật chính thống.</p>
          </div>
          <div className="feature-card">
            <h3>Dễ tiếp cận</h3>
            <p>Giao diện thân thiện, giúp mọi người đều có thể sử dụng.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;