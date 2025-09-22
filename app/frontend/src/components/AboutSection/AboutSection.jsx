import React, { useRef, useEffect, useState } from 'react';
import './AboutSection.css';
import StaticParticleBackground from '../ParticleBackground/StaticParticleBackground';

// Custom hook để theo dõi xem element có trong màn hình không
const useOnScreen = (options) => {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.unobserve(entry.target);
      }
    }, options);

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [ref, options]);

  return [ref, isVisible];
};

const AboutSection = () => {
  // Dùng custom hook để lấy ref và trạng thái isVisible
  const [ref, isVisible] = useOnScreen({ threshold: 0.2 });

  return (
    // Gán ref vào đây và thêm class 'is-visible' khi nó xuất hiện
    <section 
      ref={ref} 
      className={`about-section-container ${isVisible ? 'is-visible' : ''}`}
    >
      <StaticParticleBackground />
      <div className="about-section-content">
        <h2>Về LegalTalk</h2>
        <p>
          Một trợ lý AI thông minh, giúp bạn giải đáp các thắc mắc pháp lý trong lĩnh vực y
          tế một cách nhanh chóng và tin cậy.
        </p>
        <div className="features-grid">
          <div className="feature-card">
            <h3>Nhanh chóng</h3>
            <p>Nhận câu trả lời ngay lập tức, không cần chờ đợi.</p>
          </div>
          <div className="feature-card">
            <h3>Chính xác</h3>
            <p>Dữ liệu được huấn luyện từ các văn bản pháp luật chính thống.</p>
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