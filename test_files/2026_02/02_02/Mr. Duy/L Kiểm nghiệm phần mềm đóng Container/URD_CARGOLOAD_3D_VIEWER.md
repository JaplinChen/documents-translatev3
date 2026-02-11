# User Requirements Document (URD)
## CargoLoad 3D Viewer - Hệ thống Quản lý và Xếp hàng Container 3D

---

## 1. THÔNG TIN DỰ ÁN

**Tên dự án:** CargoLoad 3D Viewer  
**Phiên bản:** 1.0  
**Ngày tạo:** 08/12/2024  
**Người tạo:** Development Team  

---

## 2. TỔNG QUAN HỆ THỐNG

### 2.1. Mục đích
Hệ thống CargoLoad 3D Viewer là ứng dụng web cho phép người dùng:
- Quản lý thông tin container và hàng hóa
- Tự động tính toán và xếp hàng vào container tối ưu
- Trực quan hóa 3D quá trình xếp hàng
- Quản lý đơn hàng và lưu trữ bố cục xếp hàng

### 2.2. Phạm vi
- **Người dùng:** Nhân viên kho, quản lý logistics, khách hàng
- **Nền tảng:** Web Application (Desktop & Mobile)
- **Công nghệ:** Three.js, ASP.NET Core, SQL Server

---

## 3. YÊU CẦU CHỨC NĂNG

### 3.1. Quản lý Người dùng

#### 3.1.1. Đăng nhập/Đăng xuất
- **Mô tả:** Người dùng có thể đăng nhập vào hệ thống bằng email và mật khẩu
- **Yêu cầu:**
  - Xác thực thông tin đăng nhập
  - Lưu trữ session người dùng
  - Tự động đăng xuất sau thời gian không hoạt động
  - Hiển thị avatar với chữ cái đầu tên người dùng

#### 3.1.2. Phân quyền
- **Admin:** Toàn quyền quản lý hệ thống
  - Quản lý người dùng (thêm, sửa, xóa)
  - Quản lý container
  - Xem tất cả đơn hàng
- **User:** Quyền hạn cơ bản
  - Xếp hàng vào container
  - Quản lý đơn hàng của mình
  - Xem thống kê

#### 3.1.3. Đổi mật khẩu
- **Mô tả:** Người dùng có thể thay đổi mật khẩu
- **Yêu cầu:**
  - Xác thực mật khẩu hiện tại
  - Mật khẩu mới tối thiểu 6 ký tự
  - Xác nhận mật khẩu mới

---

### 3.2. Quản lý Container

#### 3.2.1. Danh sách Container
- **Mô tả:** Hiển thị danh sách các loại container có sẵn
- **Thông tin hiển thị:**
  - Tên container (20ft, 40ft, 40ft HC, 45ft HC)
  - Kích thước (Rộng x Cao x Dài)
  - Thể tích
  - Trọng tải tối đa
  - Màu sắc đại diện

#### 3.2.2. Thêm/Sửa/Xóa Container (Admin)
- **Mô tả:** Admin có thể quản lý các loại container
- **Yêu cầu:**
  - Nhập đầy đủ thông tin container
  - Validate kích thước và trọng tải
  - Xác nhận trước khi xóa

---

### 3.3. Import và Xếp hàng

#### 3.3.1. Import từ Excel
- **Mô tả:** Người dùng có thể import danh sách hàng hóa từ file Excel
- **Định dạng Excel:**
  - Tên hàng hóa
  - Chiều rộng (m)
  - Chiều cao (m)
  - Chiều dài (m)
  - Khối lượng (kg)
  - Số lượng

- **Yêu cầu:**
  - Hỗ trợ file .xlsx, .xls
  - Validate dữ liệu đầu vào
  - Hiển thị lỗi nếu dữ liệu không hợp lệ
  - Cung cấp file template mẫu

#### 3.3.2. Chọn Container
- **Mô tả:** Sau khi import, hệ thống hiển thị modal cho phép chọn loại container
- **Yêu cầu:**
  - Hiển thị danh sách container có sẵn
  - Đánh dấu container phù hợp nhất (Best Fit)
  - Cho phép chọn nhiều loại container
  - Hiển thị thông tin:
    - Tỷ lệ lấp đầy ước tính
    - Khả năng chứa hàng
    - Kích thước container

#### 3.3.3. Tự động Xếp hàng
- **Mô tả:** Hệ thống tự động tính toán và xếp hàng vào container
- **Thuật toán:** MaximalSpace Bin Packing
- **Yêu cầu:**
  - Tối ưu hóa tỷ lệ lấp đầy (>70%)
  - Tự động xoay hàng để tối ưu không gian
  - Tự động tạo thêm container nếu hàng không xếp hết
  - Xếp container theo chiều ngang (trục X)
  - Khoảng cách giữa các container: 2.5m
  - Hiển thị animation "robot đang suy nghĩ" trong quá trình tính toán

#### 3.3.4. Tự động Gen nhiều Container
- **Mô tả:** Khi hàng hóa không xếp hết vào 1 container, tự động tạo thêm container
- **Yêu cầu:**
  - Tính toán số lượng hàng còn lại chính xác
  - Tạo container mới với loại đã chọn
  - Tiếp tục xếp hàng vào container mới
  - Dừng khi xếp hết hàng hoặc đạt giới hạn (100 container)
  - Hiển thị thông báo tổng kết

---

### 3.4. Trực quan hóa 3D

#### 3.4.1. Hiển thị 3D
- **Mô tả:** Hiển thị container và hàng hóa trong không gian 3D
- **Yêu cầu:**
  - Render container với màu sắc và kích thước chính xác
  - Hiển thị hàng hóa với màu sắc theo loại
  - Hiển thị label trên mỗi kiện hàng
  - Hiển thị viền đen cho các cạnh
  - Hỗ trợ nhiều container cùng lúc

#### 3.4.2. Điều khiển Camera
- **Mô tả:** Người dùng có thể điều khiển góc nhìn 3D
- **Yêu cầu:**
  - Xoay: Kéo chuột trái
  - Zoom: Cuộn chuột (tốc độ 0.01 - chậm và mượt)
  - Giới hạn zoom: 5-30 units
  - Giới hạn góc nhìn: Không nhìn từ dưới lên
  - Nút "Đóng băng camera" để khóa/mở camera

#### 3.4.3. Tương tác với Hàng hóa
- **Mô tả:** Người dùng có thể tương tác với hàng hóa
- **Yêu cầu:**
  - Click chọn hàng hóa (highlight màu vàng)
  - Kéo thả để di chuyển hàng
  - Nút "Bỏ hàng" để xóa hàng đã chọn
  - Validate vị trí mới (không ra ngoài container, không chồng lên nhau)

---

### 3.5. Thống kê và Báo cáo

#### 3.5.1. Bảng Thống kê Hàng hóa
- **Mô tả:** Hiển thị thống kê chi tiết về hàng hóa đã xếp
- **Vị trí:** Góc dưới giữa màn hình
- **Thông tin hiển thị:**
  - Tên loại hàng hóa
  - Màu sắc đại diện
  - Số lượng đã xếp / Tổng số lượng (ví dụ: 14/20 kiện)
  - Không hiển thị phần trăm

- **Yêu cầu:**
  - Tự động cập nhật khi thêm/xóa hàng
  - Hiển thị cho tất cả container
  - Có thể cuộn khi có nhiều loại hàng
  - Chiều cao tối đa: 250px
  - Scrollbar tùy chỉnh màu xanh

#### 3.5.2. Thống kê Container
- **Mô tả:** Hiển thị thông tin về từng container
- **Thông tin:**
  - Tên container
  - Số lượng hàng trong container
  - Tỷ lệ lấp đầy
  - Thể tích đã sử dụng / Tổng thể tích

---

### 3.6. Quản lý Đơn hàng

#### 3.6.1. Lưu Đơn hàng
- **Mô tả:** Người dùng có thể lưu bố cục xếp hàng thành đơn hàng
- **Thông tin cần nhập:**
  - Tên khách hàng (bắt buộc)
  - Số điện thoại
  - Email
  - Địa chỉ giao hàng
  - Ghi chú

- **Yêu cầu:**
  - Lưu thông tin container và vị trí hàng hóa
  - Tạo mã đơn hàng tự động
  - Lưu timestamp

#### 3.6.2. Danh sách Đơn hàng
- **Mô tả:** Hiển thị danh sách các đơn hàng đã tạo
- **Thông tin hiển thị:**
  - Mã đơn hàng
  - Tên khách hàng
  - Ngày tạo
  - Số lượng container
  - Số lượng hàng hóa
  - Trạng thái

#### 3.6.3. Xem chi tiết Đơn hàng
- **Mô tả:** Người dùng có thể xem lại bố cục xếp hàng của đơn hàng
- **Yêu cầu:**
  - Tải lại container và hàng hóa vào 3D viewer
  - Hiển thị đầy đủ thông tin đơn hàng
  - Cho phép chỉnh sửa (nếu chưa hoàn thành)

---

### 3.7. Giao diện và Trải nghiệm

#### 3.7.1. Navigation
- **Mô tả:** Menu điều hướng giữa các trang
- **Các trang:**
  - 🎨 3D Workspace (Trang chính)
  - 📦 Đơn hàng
  - ⚙️ Quản lý Container
  - 👥 Người dùng (chỉ Admin)

#### 3.7.2. Control Panel
- **Mô tả:** Panel điều khiển ở góc trên trái
- **Các nút:**
  - 📥 Import: Import Excel
  - 📄 Template: Tải file mẫu
  - 🔒 Đóng băng camera: Khóa/mở camera
  - 🗑️ Bỏ hàng: Xóa hàng đã chọn (hiện khi chọn hàng)
  - 💾 Save: Lưu đơn hàng

#### 3.7.3. Toast Notification
- **Mô tả:** Thông báo ngắn ở góc trên phải
- **Loại thông báo:**
  - Success (màu xanh)
  - Error (màu đỏ)
  - Warning (màu vàng)
  - Info (màu xanh dương)

#### 3.7.4. Modal
- **Các modal:**
  - Container Selection: Chọn container
  - Save Order: Lưu đơn hàng
  - Change Password: Đổi mật khẩu
  - Thinking Robot: Animation đang tính toán

---

## 4. YÊU CẦU PHI CHỨC NĂNG

### 4.1. Hiệu năng
- **Thời gian khởi tạo:** < 3 giây
- **FPS:** ≥ 30 (ngưỡng cảnh báo)
- **Thời gian tính toán packing:** < 5 giây cho 100 kiện hàng
- **Thời gian resize:** < 200ms

### 4.2. Khả năng mở rộng
- Hỗ trợ tối đa 100 container cùng lúc
- Hỗ trợ tối đa 1000 kiện hàng
- Hỗ trợ nhiều thuật toán packing

### 4.3. Bảo mật
- Mã hóa mật khẩu (bcrypt)
- Session timeout: 30 phút
- HTTPS bắt buộc
- Validate input phía client và server

### 4.4. Tương thích
- **Trình duyệt:**
  - Chrome (phiên bản mới nhất)
  - Firefox (phiên bản mới nhất)
  - Edge (phiên bản mới nhất)
  - Safari (phiên bản mới nhất)
- **Thiết bị:**
  - Desktop (1920x1080 trở lên)
  - Tablet (768px trở lên)
  - Mobile (responsive)

### 4.5. Khả năng sử dụng
- Giao diện trực quan, dễ sử dụng
- Hỗ trợ tiếng Việt
- Hướng dẫn sử dụng rõ ràng
- Thông báo lỗi dễ hiểu

---

## 5. RÀNG BUỘC VÀ GIẢ ĐỊNH

### 5.1. Ràng buộc
- Hàng hóa phải nằm hoàn toàn trong container
- Hàng hóa không được chồng lên nhau
- Hàng hóa phải có support từ dưới (sàn hoặc hàng khác)
- Không vượt quá chiều cao container
- Không vượt quá trọng tải container

### 5.2. Giả định
- Người dùng có kết nối internet ổn định
- Người dùng có kiến thức cơ bản về logistics
- Dữ liệu Excel được chuẩn bị đúng format
- Container có hình dạng hộp chữ nhật

---

## 6. GIAO DIỆN NGƯỜI DÙNG

### 6.1. Màu sắc
- **Primary:** #11998e (xanh lá)
- **Secondary:** #38ef7d (xanh lá nhạt)
- **Success:** #2ecc71
- **Error:** #c62828
- **Warning:** #ffc107
- **Info:** #3498db

### 6.2. Typography
- **Font:** System fonts (Arial, Helvetica, sans-serif)
- **Heading:** 18-24px, font-weight: 600
- **Body:** 14px, font-weight: 400
- **Small:** 12px

### 6.3. Layout
- **Header:** 60px height, gradient background
- **Sidebar:** 250px width (nếu có)
- **Main content:** Chiếm toàn bộ không gian còn lại
- **Footer:** Không có

---

## 7. LUỒNG NGHIỆP VỤ CHÍNH

### 7.1. Luồng Xếp hàng cơ bản
1. Người dùng đăng nhập
2. Vào trang "3D Workspace"
3. Click nút "Import"
4. Chọn file Excel
5. Hệ thống hiển thị modal chọn container
6. Người dùng chọn loại container
7. Click "Tính toán & Xếp hàng"
8. Hệ thống hiển thị robot đang suy nghĩ
9. Hệ thống tự động:
   - Tạo container đầu tiên
   - Xếp hàng vào container
   - Nếu còn hàng, tạo container thứ 2
   - Tiếp tục cho đến khi hết hàng
10. Hiển thị kết quả 3D
11. Hiển thị thống kê
12. Người dùng có thể:
    - Xem 3D (xoay, zoom)
    - Điều chỉnh vị trí hàng (kéo thả)
    - Lưu đơn hàng

### 7.2. Luồng Quản lý Đơn hàng
1. Người dùng vào trang "Đơn hàng"
2. Xem danh sách đơn hàng
3. Click vào đơn hàng để xem chi tiết
4. Hệ thống tải lại bố cục 3D
5. Người dùng có thể:
   - Xem thông tin đơn hàng
   - Chỉnh sửa (nếu chưa hoàn thành)
   - Xuất báo cáo

---

## 8. TIÊU CHÍ CHẤP NHẬN

### 8.1. Chức năng
- ✅ Tất cả chức năng hoạt động đúng theo mô tả
- ✅ Không có lỗi critical
- ✅ Xử lý lỗi gracefully

### 8.2. Hiệu năng
- ✅ Đạt các chỉ số hiệu năng yêu cầu
- ✅ Không lag khi thao tác 3D
- ✅ Load trang nhanh

### 8.3. Giao diện
- ✅ Giao diện đẹp, trực quan
- ✅ Responsive trên các thiết bị
- ✅ Không có lỗi hiển thị

### 8.4. Bảo mật
- ✅ Không có lỗ hổng bảo mật
- ✅ Dữ liệu được mã hóa
- ✅ Phân quyền chính xác

---

## 9. PHỤ LỤC

### 9.1. Thuật ngữ
- **Container:** Thùng chứa hàng hóa (20ft, 40ft, 45ft HC)
- **Cargo:** Hàng hóa, kiện hàng
- **Packing:** Quá trình xếp hàng vào container
- **Fill Rate:** Tỷ lệ lấp đầy container
- **MaximalSpace:** Thuật toán tối ưu hóa không gian

### 9.2. Tài liệu tham khảo
- Three.js Documentation
- ASP.NET Core Documentation
- Bin Packing Algorithms

---

**Phê duyệt:**

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|--------|--------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |

---

*Tài liệu này có thể được cập nhật theo yêu cầu thay đổi của dự án.*
