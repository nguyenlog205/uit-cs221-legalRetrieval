# Frontend - LegalTalk Chatbot

Đây là thư mục chứa toàn bộ mã nguồn cho phần giao diện người dùng (UI) của dự án LegalTalk, được xây dựng bằng React và Vite.

## ✨ Tính năng chính

* Giao diện đa trang (Trang chủ, Trang Chat) sử dụng `react-router-dom`.
* Chế độ Sáng/Tối (Light/Dark Mode) được lưu lại cho người dùng.
* Giao diện chat tương tác, tự động cuộn và kết nối với API backend.
* Các hiệu ứng động tinh tế để tăng trải nghiệm người dùng.

## 🚀 Công nghệ sử dụng

* **Framework:** [React](https://reactjs.org/) (với Vite)
* **Routing:** [React Router DOM](https://reactrouter.com/)
* **Gọi API:** [Axios](https://axios-http.com/)
* **Hiệu ứng:** [React Particles](https://particles.js.org/) (cho `tsparticles-slim`)
* **Styling:** CSS Modules

## ⚙️ Cài đặt và Chạy

### Yêu cầu
* [Node.js](https://nodejs.org/) (phiên bản 18.x trở lên)
* [npm](https://www.npmjs.com/)

### Chạy ở môi trường phát triển (Development)

1.  **Di chuyển vào thư mục frontend:**
    ```bash
    cd app/frontend
    ```

2.  **Cài đặt các thư viện cần thiết:**
    Lệnh này sẽ đọc file `package.json` và tải về các thư viện.
    ```bash
    npm install
    ```

3.  **Khởi động server phát triển:**
    ```bash
    npm run dev
    ```
    Ứng dụng sẽ tự động mở và chạy tại địa chỉ `http://localhost:5173`.

### Build cho môi trường Production

Để tạo phiên bản tối ưu cho việc deploy, chạy lệnh sau:
```bash
npm run build
```
Lệnh này sẽ tạo ra một thư mục `dist` chứa tất cả các file tĩnh đã được tối ưu.

### 🐳 Chạy bằng Docker
Để chạy frontend một cách độc lập bằng Docker (sau khi đã build image):
```bash
# Build Docker image từ Dockerfile trong thư mục này
docker build -t legaltalk-frontend .

# Chạy container từ image vừa tạo
docker run -p 5173:80 legaltalk-frontend
```
Truy cập ứng dụng tại `http://localhost:5173`.

Lưu ý: Cách tốt nhất để chạy toàn bộ dự án là sử dụng file `docker-compose.yml` ở thư mục gốc.