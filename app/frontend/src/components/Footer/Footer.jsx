import React from 'react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer-container">
      <div className="footer-content">
        <div className="footer-column">
          <h4>Về LegalTalk</h4>
          <p>Hệ thống hỗ trợ thủ tục hành chính và pháp lý trong y tế, được phát triển cho đồ án môn học <strong>CS221 - Xử lý ngôn ngữ tự nhiên</strong> tại <strong>trường Đại học Công nghệ Thông tin, ĐHQG-HCM</strong>.</p>
        </div>

        <div className="footer-column">
          <h4>Đội ngũ phát triển</h4>
          <ul>
            <li>
              <strong>Lê Nguyễn Quỳnh Như</strong> - 23521123
              <br />
              <small>Khoa Khoa học Máy tính</small>
            </li>
            <li>
              <strong>Nguyễn Hoàng Long</strong> - 23520882
              <br />
              <small>Khoa Khoa học và Kỹ thuật Thông tin</small>
            </li>
            <li>
              <strong>Hồ Tấn Dũng</strong> - 23520327
              <br />
              <small>Khoa Khoa học và Kỹ thuật Thông tin</small>
            </li>
          </ul>
        </div>

        <div className="footer-column">
          <h4>Lời cảm ơn</h4>
          <p>Xin chân thành cảm ơn sự hướng dẫn tận tình của giảng viên,<strong> ThS. Nguyễn Trọng Chỉnh</strong>, Khoa Khoa học Máy tính, trường Đại học Công nghệ Thông tin, ĐHQG-HCM.</p>
        </div>
      </div>
      <div className="footer-copyright">
        <p>© 2025 LegalTalk Team. All Rights Reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;