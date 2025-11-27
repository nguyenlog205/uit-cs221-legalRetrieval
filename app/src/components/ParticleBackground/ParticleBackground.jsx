import React, { useCallback } from 'react';
import Particles from 'react-particles';
import { loadSlim } from 'tsparticles-slim';

const ParticleBackground = () => {
  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine);
  }, []);

  const particleOptions = {
    // FIX 1: Luôn hiển thị & full màn hình
    // Tùy chọn này sẽ buộc canvas chiếm toàn bộ màn hình và nằm ở lớp nền z-index: -1
    // Giúp giải quyết vấn đề "chỉ hiển thị một tí"
    fullScreen: {
      enable: true,
      zIndex: -1,
    },
    
    fpsLimit: 60,
    interactivity: {
      events: {
        onHover: {
          enable: true,
          // FIX 4: Hiệu ứng mờ dần khi xa chuột
          // Chuyển từ "grab" sang "bubble" để có thể tùy chỉnh độ mờ
          mode: 'bubble',
        },
        resize: true,
      },
      modes: {
        // Cấu hình cho hiệu ứng "bubble" khi di chuột
        bubble: {
          distance: 250, // Khoảng cách ảnh hưởng từ con chuột
          duration: 2,
          opacity: 1, // Di chuột vào sẽ làm các hạt rõ lên 100%
          size: 3,
        },
      },
    },
    particles: {
      color: {
        value: 'rgba(0, 90, 158, 0.5)',
      },
      links: {
        color: 'rgba(0, 90, 158, 0.4)',
        distance: 150,
        enable: true,
        // FIX 3: Mờ hơn nữa
        opacity: 0.15, // Giảm độ mờ của đường nối
        width: 1,
      },
      collisions: {
        enable: false, // Tắt va chạm để trông mượt hơn
      },
      move: {
        direction: 'none',
        enable: true,
        outModes: {
          default: 'bounce',
        },
        random: true, // Cho các hạt di chuyển ngẫu nhiên hơn
        speed: 0.5, // Giảm tốc độ
        straight: false,
      },
      number: {
        density: {
          enable: true,
          area: 800,
        },
        value: 50, // Giảm số lượng hạt một chút
      },
      // FIX 3: Mờ hơn nữa
      opacity: {
        value: 0.2, // Giảm độ mờ của hạt
      },
      shape: {
        type: 'circle',
      },
      // FIX 2: Size nhỏ hơn
      size: {
        value: { min: 1, max: 2 }, // Giảm kích thước hạt
      },
    },
    detectRetina: true,
  };

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={particleOptions}
    />
  );
};

export default ParticleBackground;