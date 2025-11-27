import React, { useCallback } from 'react';
import Particles from 'react-particles';
import { loadSlim } from 'tsparticles-slim';

const StaticParticleBackground = () => {
  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine);
  }, []);

  const particleOptions = {
    // Không fullScreen, sẽ được định vị bởi CSS của component cha
    fullScreen: {
      enable: false,
    },
    fpsLimit: 30, // Giảm FPS để nhẹ hơn
    interactivity: {
      events: {
        onHover: {
          enable: false, // TẮT tương tác chuột
        },
        onClick: {
          enable: false, // TẮT tương tác click
        },
        resize: true,
      },
    },
    particles: {
      color: {
        value: 'rgba(0, 90, 158, 0.2)', // Màu xanh mờ hơn nữa
      },
      links: {
        color: 'rgba(0, 90, 158, 0.1)', // Đường nối cực mờ
        distance: 120, // Khoảng cách nối ngắn hơn
        enable: true,
        opacity: 0.05, // Độ mờ của đường nối
        width: 1,
      },
      collisions: {
        enable: false,
      },
      move: {
        direction: 'none',
        enable: true,
        outModes: {
          default: 'bounce',
        },
        random: true,
        speed: 0.1, // Tốc độ cực chậm
        straight: false,
      },
      number: {
        density: {
          enable: true,
          area: 800,
        },
        value: 40, // Số lượng hạt vừa phải
      },
      opacity: {
        value: 0.1, // Độ mờ của hạt
      },
      shape: {
        type: 'circle',
      },
      size: {
        value: { min: 0.5, max: 1.5 }, // Kích thước hạt rất nhỏ
      },
    },
    detectRetina: true,
  };

  return (
    <Particles
      id="static-tsparticles" // ID khác để tránh xung đột
      init={particlesInit}
      options={particleOptions}
    />
  );
};

export default StaticParticleBackground;