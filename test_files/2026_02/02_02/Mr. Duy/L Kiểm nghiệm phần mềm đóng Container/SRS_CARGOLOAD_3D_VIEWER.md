# Software Requirements Specification (SRS)
## CargoLoad 3D Viewer - Hệ thống Quản lý và Xếp hàng Container 3D

---

## 1. GIỚI THIỆU

### 1.1. Mục đích
Tài liệu này mô tả chi tiết các yêu cầu chức năng và phi chức năng của hệ thống CargoLoad 3D Viewer. Tài liệu này dành cho:
- Đội ngũ phát triển
- Đội ngũ kiểm thử
- Quản lý dự án
- Stakeholders

### 1.2. Phạm vi
CargoLoad 3D Viewer là hệ thống web application cho phép:
- Quản lý thông tin container và hàng hóa
- Tự động tính toán và xếp hàng tối ưu
- Trực quan hóa 3D quá trình xếp hàng
- Quản lý đơn hàng và người dùng

### 1.3. Định nghĩa và Từ viết tắt
- **API:** Application Programming Interface
- **3D:** Three Dimensional
- **UI:** User Interface
- **UX:** User Experience
- **CRUD:** Create, Read, Update, Delete
- **JWT:** JSON Web Token
- **SPA:** Single Page Application

### 1.4. Tài liệu tham khảo
- URD_CARGOLOAD_3D_VIEWER.md
- CAU_TRUC_DATABASE.md
- Three.js Documentation
- ASP.NET Core Documentation

---

## 2. MÔ TẢ TỔNG QUAN

### 2.1. Góc nhìn sản phẩm
CargoLoad 3D Viewer là hệ thống độc lập, hoạt động trên nền tảng web, sử dụng kiến trúc Client-Server với:
- **Frontend:** HTML5, CSS3, JavaScript (Three.js)
- **Backend:** ASP.NET Core Web API
- **Database:** SQL Server
- **Authentication:** JWT Token

### 2.2. Chức năng sản phẩm
1. Quản lý người dùng và phân quyền
2. Quản lý container
3. Import hàng hóa từ Excel
4. Tự động xếp hàng với thuật toán tối ưu
5. Trực quan hóa 3D
6. Quản lý đơn hàng
7. Thống kê và báo cáo

### 2.3. Đặc điểm người dùng
- **Admin:** Quản trị viên hệ thống, có kiến thức IT
- **User:** Nhân viên kho, quản lý logistics, có kiến thức cơ bản về máy tính

### 2.4. Ràng buộc
- Yêu cầu trình duyệt hỗ trợ WebGL
- Kết nối internet ổn định
- Độ phân giải màn hình tối thiểu 1366x768

---

## 3. YÊU CẦU CỤ THỂ

### 3.1. Yêu cầu Chức năng

#### 3.1.1. Module Xác thực và Phân quyền

**FR-AUTH-001: Đăng nhập**
- **Mô tả:** Người dùng đăng nhập bằng email và mật khẩu
- **Input:** Email, Password
- **Process:**
  1. Validate format email
  2. Kiểm tra email tồn tại trong database
  3. Verify password (bcrypt)
  4. Tạo JWT token
  5. Lưu token vào localStorage
- **Output:** JWT token, thông tin user
- **Validation:**
  - Email: Required, Email format
  - Password: Required, Min 6 characters
- **Error Handling:**
  - Email không tồn tại: "Email không tồn tại"
  - Sai mật khẩu: "Mật khẩu không đúng"
  - Server error: "Lỗi hệ thống, vui lòng thử lại"

**FR-AUTH-002: Đăng xuất**
- **Mô tả:** Người dùng đăng xuất khỏi hệ thống
- **Process:**
  1. Xóa token khỏi localStorage
  2. Redirect về trang login
- **Output:** Redirect to login page

**FR-AUTH-003: Đổi mật khẩu**
- **Mô tả:** Người dùng thay đổi mật khẩu
- **Input:** Current Password, New Password, Confirm Password
- **Process:**
  1. Verify current password
  2. Validate new password
  3. Check new password = confirm password
  4. Hash new password
  5. Update database
- **Validation:**
  - Current Password: Required
  - New Password: Required, Min 6 characters
  - Confirm Password: Required, Must match New Password
- **Error Handling:**
  - Sai mật khẩu hiện tại: "Mật khẩu hiện tại không đúng"
  - Mật khẩu mới không khớp: "Mật khẩu xác nhận không khớp"

**FR-AUTH-004: Phân quyền**
- **Mô tả:** Hệ thống phân quyền theo role
- **Roles:**
  - Admin: Full access
  - User: Limited access
- **Access Control:**
  - Admin: Tất cả chức năng
  - User: Không thể quản lý users, containers

#### 3.1.2. Module Quản lý Container

**FR-CONT-001: Xem danh sách Container**
- **Mô tả:** Hiển thị danh sách các loại container
- **Output:** List of containers with:
  - ID, Name, Type
  - Width, Height, Depth (meters)
  - Volume (m³)
  - Max Weight (kg)
  - Color
- **Sorting:** By name (default)
- **Pagination:** 10 items per page

**FR-CONT-002: Thêm Container (Admin only)**
- **Mô tả:** Admin thêm loại container mới
- **Input:**
  - Name (Required, Max 100 chars)
  - Type (Required, Max 50 chars)
  - Width (Required, > 0)
  - Height (Required, > 0)
  - Depth (Required, > 0)
  - Max Weight (Required, > 0)
  - Color (Required, Hex format)
- **Process:**
  1. Validate input
  2. Check duplicate name
  3. Calculate volume
  4. Save to database
- **Output:** Success message, new container ID
- **Error Handling:**
  - Duplicate name: "Tên container đã tồn tại"
  - Invalid dimensions: "Kích thước không hợp lệ"

**FR-CONT-003: Sửa Container (Admin only)**
- **Mô tả:** Admin cập nhật thông tin container
- **Input:** Container ID + Updated fields
- **Process:** Similar to FR-CONT-002
- **Output:** Success message

**FR-CONT-004: Xóa Container (Admin only)**
- **Mô tả:** Admin xóa container
- **Input:** Container ID
- **Process:**
  1. Check if container is used in orders
  2. If used, prevent deletion
  3. If not used, delete from database
- **Output:** Success message
- **Error Handling:**
  - Container in use: "Không thể xóa container đang được sử dụng"

#### 3.1.3. Module Import và Xếp hàng

**FR-PACK-001: Import Excel**
- **Mô tả:** Import danh sách hàng hóa từ Excel
- **Input:** Excel file (.xlsx, .xls)
- **Excel Format:**
  - Column 1: Tên (Text)
  - Column 2: Chiều rộng (m) (Number)
  - Column 3: Chiều cao (m) (Number)
  - Column 4: Chiều dài (m) (Number)
  - Column 5: Khối lượng (kg) (Number)
  - Column 6: Số lượng (Integer)
- **Process:**
  1. Read Excel file using SheetJS
  2. Parse data to JSON
  3. Validate each row
  4. Return cargo list
- **Output:** Array of cargo items
- **Validation:**
  - All dimensions > 0
  - Quantity > 0
  - Max 1000 items
- **Error Handling:**
  - Invalid file format: "File không đúng định dạng"
  - Invalid data: "Dòng X: [error message]"
  - File too large: "File quá lớn (max 5MB)"

**FR-PACK-002: Chọn Container**
- **Mô tả:** Hiển thị modal cho phép chọn container
- **Input:** Cargo list from FR-PACK-001
- **Process:**
  1. Load available containers from API
  2. Calculate best fit for each container
  3. Display containers with fit info
  4. Allow multiple selection
- **Output:** Array of selected container types
- **Display Info:**
  - Container name, dimensions
  - Estimated fill rate
  - Can fit / Cannot fit
  - Best fit badge (if applicable)

**FR-PACK-003: Tự động Xếp hàng**
- **Mô tả:** Tự động tính toán và xếp hàng vào container
- **Input:**
  - Cargo list
  - Selected container types
- **Algorithm:** MaximalSpace Bin Packing
- **Process:**
  1. Show "Thinking Robot" animation
  2. Create first container
  3. Run packing algorithm
  4. Place cargo in 3D scene
  5. If cargo remains:
     - Create next container
     - Continue packing
  6. Repeat until all cargo placed or limit reached
- **Output:**
  - 3D visualization
  - Statistics panel
  - Success/Warning message
- **Constraints:**
  - Max 100 containers
  - Cargo must fit in container bounds
  - No overlapping
  - Support from below required
- **Performance:**
  - < 5 seconds for 100 items
  - Show progress for large datasets

**FR-PACK-004: Tự động Gen nhiều Container**
- **Mô tả:** Tự động tạo thêm container khi cần
- **Process:**
  1. Pack cargo into current container
  2. Count successfully placed items
  3. Calculate remaining cargo
  4. If remaining > 0:
     - Create new container (next in selected types)
     - Position at X = previous containers + spacing
     - Continue packing
  5. Repeat until done
- **Spacing:** 2.5m between containers
- **Positioning:** Along X axis (horizontal)

#### 3.1.4. Module Trực quan hóa 3D

**FR-3D-001: Render 3D Scene**
- **Mô tả:** Hiển thị container và hàng hóa trong 3D
- **Technology:** Three.js
- **Components:**
  - Scene, Camera, Renderer
  - Lighting (Ambient + Directional)
  - Grid helper
  - Containers (BoxGeometry)
  - Cargo boxes (BoxGeometry with edges)
- **Performance:**
  - Target FPS: 60
  - Min FPS: 30
  - Use requestAnimationFrame

**FR-3D-002: Camera Controls**
- **Mô tả:** Điều khiển góc nhìn 3D
- **Controls:** OrbitControls
- **Features:**
  - Rotate: Left mouse drag
  - Zoom: Mouse wheel (speed: 0.01)
  - Pan: Disabled
  - Damping: Enabled (0.05)
- **Limits:**
  - Min distance: 5 units
  - Max distance: 30 units
  - Min polar angle: 0
  - Max polar angle: π/2 (không nhìn từ dưới)
- **Freeze Camera:** Button to lock/unlock camera

**FR-3D-003: Cargo Interaction**
- **Mô tả:** Tương tác với hàng hóa
- **Features:**
  - Click to select (highlight yellow)
  - Drag to move
  - Delete selected cargo
- **Validation:**
  - New position must be in container
  - No overlapping with other cargo
  - Must have support below
- **Visual Feedback:**
  - Selected: Yellow outline
  - Valid position: Green preview
  - Invalid position: Red preview

**FR-3D-004: Multiple Containers Display**
- **Mô tả:** Hiển thị nhiều container cùng lúc
- **Layout:** Horizontal (along X axis)
- **Spacing:** 2.5m between containers
- **Camera:** Auto-adjust to fit all containers

#### 3.1.5. Module Thống kê

**FR-STAT-001: Bảng Thống kê Hàng hóa**
- **Mô tả:** Hiển thị thống kê chi tiết
- **Position:** Bottom center
- **Data:**
  - Cargo type name
  - Color indicator
  - Placed / Total quantity
  - No percentage
- **Features:**
  - Auto-update on cargo changes
  - Scrollable (max height: 250px)
  - Custom scrollbar (green)
- **Calculation:**
  - Count all cargo in scene by type
  - Compare with original Excel data

**FR-STAT-002: Container Statistics**
- **Mô tả:** Thống kê từng container
- **Data:**
  - Container name
  - Cargo count
  - Fill rate (%)
  - Used volume / Total volume

#### 3.1.6. Module Quản lý Đơn hàng

**FR-ORD-001: Lưu Đơn hàng**
- **Mô tả:** Lưu bố cục xếp hàng thành đơn hàng
- **Input:**
  - Customer Name (Required)
  - Phone (Optional)
  - Email (Optional)
  - Shipping Address (Optional)
  - Notes (Optional)
- **Process:**
  1. Validate input
  2. Generate order number
  3. Save order info
  4. Save cargo positions
  5. Save container info
- **Output:** Order ID, success message

**FR-ORD-002: Danh sách Đơn hàng**
- **Mô tả:** Hiển thị danh sách đơn hàng
- **Display:**
  - Order number
  - Customer name
  - Created date
  - Container count
  - Cargo count
  - Status
- **Sorting:** By created date (newest first)
- **Pagination:** 20 items per page
- **Filter:** By status, date range

**FR-ORD-003: Xem chi tiết Đơn hàng**
- **Mô tả:** Xem lại bố cục xếp hàng
- **Process:**
  1. Load order data from API
  2. Recreate containers in 3D
  3. Recreate cargo at saved positions
  4. Display order info
- **Features:**
  - View-only mode
  - Export to PDF (future)

---

### 3.2. Yêu cầu Giao diện

#### 3.2.1. Thiết kế Tổng quan
- **Layout:** Single Page Application (SPA)
- **Navigation:** Top tab bar
- **Responsive:** Desktop, Tablet, Mobile
- **Theme:** Modern, clean, professional

#### 3.2.2. Màu sắc
- Primary: #11998e
- Secondary: #38ef7d
- Success: #2ecc71
- Error: #c62828
- Warning: #ffc107
- Info: #3498db
- Background: #f5f5f5
- Text: #333333

#### 3.2.3. Typography
- Font Family: System fonts
- Heading: 18-24px, Bold
- Body: 14px, Regular
- Small: 12px, Regular

#### 3.2.4. Components
- Buttons: Rounded (8px), Gradient background
- Inputs: Border radius 8px, Focus state
- Modals: Centered, Backdrop blur
- Toast: Top right, Auto-dismiss (3s)
- Tables: Striped rows, Hover effect

---

### 3.3. Yêu cầu Phi chức năng

#### 3.3.1. Hiệu năng
- **NFR-PERF-001:** Thời gian load trang < 3 giây
- **NFR-PERF-002:** FPS ≥ 30 khi render 3D
- **NFR-PERF-003:** Thời gian packing < 5 giây cho 100 items
- **NFR-PERF-004:** API response time < 500ms
- **NFR-PERF-005:** Database query time < 100ms

#### 3.3.2. Bảo mật
- **NFR-SEC-001:** Mã hóa mật khẩu bằng bcrypt
- **NFR-SEC-002:** Sử dụng JWT cho authentication
- **NFR-SEC-003:** HTTPS bắt buộc
- **NFR-SEC-004:** Validate input phía client và server
- **NFR-SEC-005:** Session timeout: 30 phút
- **NFR-SEC-006:** SQL injection prevention
- **NFR-SEC-007:** XSS prevention

#### 3.3.3. Khả năng mở rộng
- **NFR-SCAL-001:** Hỗ trợ 100 concurrent users
- **NFR-SCAL-002:** Hỗ trợ 1000 cargo items
- **NFR-SCAL-003:** Hỗ trợ 100 containers cùng lúc
- **NFR-SCAL-004:** Database size: 10GB

#### 3.3.4. Độ tin cậy
- **NFR-REL-001:** Uptime: 99.5%
- **NFR-REL-002:** Backup database hàng ngày
- **NFR-REL-003:** Error logging và monitoring
- **NFR-REL-004:** Graceful error handling

#### 3.3.5. Khả năng sử dụng
- **NFR-USA-001:** Giao diện trực quan, dễ hiểu
- **NFR-USA-002:** Thông báo lỗi rõ ràng
- **NFR-USA-003:** Hỗ trợ tiếng Việt
- **NFR-USA-004:** Responsive design
- **NFR-USA-005:** Keyboard shortcuts (future)

#### 3.3.6. Tương thích
- **NFR-COMP-001:** Chrome (latest)
- **NFR-COMP-002:** Firefox (latest)
- **NFR-COMP-003:** Edge (latest)
- **NFR-COMP-004:** Safari (latest)
- **NFR-COMP-005:** WebGL support required

#### 3.3.7. Bảo trì
- **NFR-MAIN-001:** Code documentation
- **NFR-MAIN-002:** Modular architecture
- **NFR-MAIN-003:** Version control (Git)
- **NFR-MAIN-004:** Automated testing (future)

---

## 4. RÀNG BUỘC HỆ THỐNG

### 4.1. Ràng buộc Kỹ thuật
- Phải sử dụng ASP.NET Core 6.0+
- Phải sử dụng SQL Server 2019+
- Phải sử dụng Three.js cho 3D rendering
- Phải hỗ trợ WebGL

### 4.2. Ràng buộc Nghiệp vụ
- Hàng hóa phải nằm trong container
- Hàng hóa không được chồng lên nhau
- Hàng hóa phải có support từ dưới
- Không vượt quá trọng tải container

### 4.3. Ràng buộc Môi trường
- Yêu cầu kết nối internet
- Yêu cầu trình duyệt hiện đại
- Độ phân giải tối thiểu: 1366x768

---

## 5. MA TRẬN TRUY VẾT

| Requirement ID | URD Section | Test Case ID | Priority |
|----------------|-------------|--------------|----------|
| FR-AUTH-001 | 3.1.1 | TC-AUTH-001 | High |
| FR-AUTH-002 | 3.1.1 | TC-AUTH-002 | High |
| FR-AUTH-003 | 3.1.3 | TC-AUTH-003 | Medium |
| FR-CONT-001 | 3.2.1 | TC-CONT-001 | High |
| FR-PACK-001 | 3.3.1 | TC-PACK-001 | High |
| FR-PACK-003 | 3.3.3 | TC-PACK-003 | Critical |
| FR-3D-001 | 3.4.1 | TC-3D-001 | Critical |
| FR-STAT-001 | 3.5.1 | TC-STAT-001 | High |
| FR-ORD-001 | 3.6.1 | TC-ORD-001 | High |

---

## 6. PHỤ LỤC

### 6.1. Thuật toán MaximalSpace Bin Packing
- Sắp xếp cargo theo thể tích (lớn → nhỏ)
- Tìm vị trí tối ưu cho mỗi cargo
- Cho phép xoay cargo để tối ưu không gian
- Tính toán maximal space sau mỗi lần đặt

### 6.2. Công thức Tính toán
- **Volume:** Width × Height × Depth
- **Fill Rate:** (Used Volume / Total Volume) × 100%
- **Weight Distribution:** Check center of gravity

---

**Phê duyệt:**

| Vai trò | Họ tên | Chữ ký | Ngày |
|---------|--------|--------|------|
| Requirements Engineer | | | |
| Technical Lead | | | |
| Product Owner | | | |

---

*Phiên bản: 1.0*  
*Ngày cập nhật: 12/12/2024*
