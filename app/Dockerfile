# --- GIAI ĐOẠN 1: Build ứng dụng React ---
# Dùng image Node.js phiên bản 18, loại "alpine" cho nhẹ
FROM node:18-alpine As build

# Đặt thư mục làm việc là /app
WORKDIR /app

# Copy file package.json và package-lock.json vào trước
# -> Tận dụng cache của Docker, nếu 2 file này không đổi thì không cần npm install lại
COPY package*.json ./

# Cài đặt các thư viện từ package.json
RUN npm install

# Copy toàn bộ source code còn lại
COPY . .

# Chạy lệnh build của React, tạo ra thư mục "dist"
RUN npm run build


# --- GIAI ĐOẠN 2: Serve ứng dụng bằng Nginx ---
# Dùng image Nginx siêu nhẹ
FROM nginx:stable-alpine

# Copy các file tĩnh đã được build ở Giai đoạn 1 vào thư mục web của Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy file cấu hình Nginx để React Router hoạt động đúng
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Mở cổng 80 (cổng mặc định của web server)
EXPOSE 80

# Lệnh để khởi động Nginx
CMD ["nginx", "-g", "daemon off;"]