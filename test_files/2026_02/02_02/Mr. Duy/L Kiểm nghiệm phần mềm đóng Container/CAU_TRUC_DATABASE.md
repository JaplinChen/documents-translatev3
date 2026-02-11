# Cấu trúc Database - Hệ thống Quản lý Xếp Container

## Sơ đồ quan hệ

```
┌─────────────────┐
│     User        │
│  (Người dùng)   │
└────────┬────────┘
         │ CreatedBy
         │
         ▼
┌─────────────────┐       ┌──────────────────┐
│     Order       │──────▶│     Layout       │
│  (Đơn hàng)     │       │  (Bố cục xếp)    │
└─────────────────┘       └────────┬─────────┘
                                   │
                          ┌────────┴────────┐
                          │                 │
                          ▼                 ▼
                  ┌──────────────┐  ┌──────────────┐
                  │  Container   │  │    Cargo     │
                  │ (Container)  │  │ (Kiện hàng)  │
                  └──────────────┘  └──────────────┘
```

## Chi tiết các bảng

### 1. User (Người dùng)
```sql
CREATE TABLE Users (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Username NVARCHAR(100) NOT NULL UNIQUE,
    Email NVARCHAR(100) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(MAX) NOT NULL,
    FullName NVARCHAR(200),
    Role NVARCHAR(50) NOT NULL, -- Admin, User
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL,
    UpdatedAt DATETIME2 NOT NULL
)
```

**Mục đích**: Quản lý người dùng hệ thống

**Quan hệ**:
- 1 User có thể tạo nhiều Orders (1-N)

---

### 2. Container (Container)
```sql
CREATE TABLE Containers (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(200) NOT NULL,
    Type NVARCHAR(100) NOT NULL, -- 20ft Standard, 40ft HC, 45ft HC
    Width DECIMAL(18,2) NOT NULL, -- Chiều rộng (m)
    Height DECIMAL(18,2) NOT NULL, -- Chiều cao (m)
    Depth DECIMAL(18,2) NOT NULL, -- Chiều dài (m)
    MaxWeight DECIMAL(18,2) NOT NULL, -- Tải trọng tối đa (kg)
    Color NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME2 NOT NULL,
    UpdatedAt DATETIME2 NOT NULL
)
```

**Mục đích**: Lưu thông tin các loại container có sẵn

**Ví dụ dữ liệu**:
```
Id: 1
Name: Container 45ft HC
Type: 45ft High Cube
Width: 2.352m
Height: 2.698m
Depth: 13.556m
MaxWeight: 27,600 kg
```

**Quan hệ**:
- 1 Container có thể được sử dụng trong nhiều Layouts (1-N)

---

### 3. Layout (Bố cục xếp hàng)
```sql
CREATE TABLE Layouts (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(200) NOT NULL,
    ContainerId INT NOT NULL,
    FillRate DECIMAL(5,2) NOT NULL, -- Tỷ lệ lấp đầy (%)
    TotalCargos INT NOT NULL, -- Tổng số kiện hàng
    CreatedAt DATETIME2 NOT NULL,
    UpdatedAt DATETIME2 NOT NULL,
    
    FOREIGN KEY (ContainerId) REFERENCES Containers(Id)
)
```

**Mục đích**: Lưu thông tin về một lần xếp hàng vào container

**Ví dụ dữ liệu**:
```
Id: 1
Name: Layout - Đơn hàng Nguyễn Văn A
ContainerId: 1
FillRate: 75.5%
TotalCargos: 10
CreatedAt: 2024-11-21 10:30:00
```

**Quan hệ**:
- 1 Layout thuộc về 1 Container (N-1)
- 1 Layout có nhiều Cargos (1-N)
- 1 Layout được sử dụng bởi 1 Order (1-1)

---

### 4. Cargo (Kiện hàng)
```sql
CREATE TABLE Cargos (
    Id INT PRIMARY KEY IDENTITY(1,1),
    LayoutId INT NOT NULL,
    
    -- Kích thước
    Width DECIMAL(18,2) NOT NULL,
    Height DECIMAL(18,2) NOT NULL,
    Depth DECIMAL(18,2) NOT NULL,
    
    -- Vị trí trong container
    PositionX DECIMAL(18,2) NOT NULL,
    PositionY DECIMAL(18,2) NOT NULL,
    PositionZ DECIMAL(18,2) NOT NULL,
    
    -- Góc xoay (radians)
    RotationX DECIMAL(18,2) NOT NULL,
    RotationY DECIMAL(18,2) NOT NULL,
    RotationZ DECIMAL(18,2) NOT NULL,
    
    -- Thông tin khác
    Color NVARCHAR(50) NOT NULL,
    Label NVARCHAR(100),
    Weight DECIMAL(18,2), -- Trọng lượng (kg)
    
    CreatedAt DATETIME2 NOT NULL,
    
    FOREIGN KEY (LayoutId) REFERENCES Layouts(Id) ON DELETE CASCADE
)
```

**Mục đích**: Lưu chi tiết từng kiện hàng trong layout

**Ví dụ dữ liệu**:
```
Id: 1
LayoutId: 1
Width: 1.0m
Height: 1.0m
Depth: 1.0m
PositionX: 0.5
PositionY: 0.5
PositionZ: 0.5
RotationX: 0
RotationY: 0
RotationZ: 0
Color: #ff6b6b
Label: Cargo 1
Weight: 100kg
```

**Quan hệ**:
- 1 Cargo thuộc về 1 Layout (N-1)
- Khi xóa Layout, tất cả Cargos liên quan cũng bị xóa (CASCADE)

---

### 5. Order (Đơn hàng)
```sql
CREATE TABLE Orders (
    Id INT PRIMARY KEY IDENTITY(1,1),
    OrderNumber NVARCHAR(50) NOT NULL UNIQUE, -- Mã đơn hàng tự động
    CustomerName NVARCHAR(200) NOT NULL, -- Tên khách hàng/đơn hàng
    CustomerPhone NVARCHAR(20),
    CustomerEmail NVARCHAR(100),
    ShippingAddress NVARCHAR(500),
    LayoutId INT NOT NULL,
    Status NVARCHAR(50) NOT NULL, -- Pending, Processing, Completed, Cancelled
    TotalWeight DECIMAL(18,2) NOT NULL, -- Tổng trọng lượng
    TotalItems INT NOT NULL, -- Tổng số kiện
    Notes NVARCHAR(MAX),
    CreatedBy INT NOT NULL,
    CreatedAt DATETIME2 NOT NULL,
    UpdatedAt DATETIME2 NOT NULL,
    
    FOREIGN KEY (LayoutId) REFERENCES Layouts(Id),
    FOREIGN KEY (CreatedBy) REFERENCES Users(Id)
)
```

**Mục đích**: Lưu thông tin đơn hàng và liên kết với layout đã xếp

**Ví dụ dữ liệu**:
```
Id: 1
OrderNumber: ORD20241121001
CustomerName: Đơn hàng Nguyễn Văn A
CustomerPhone: 0912345678
CustomerEmail: nguyenvana@email.com
ShippingAddress: 123 Đường ABC, Quận 1, TP.HCM
LayoutId: 1
Status: Pending
TotalWeight: 1000kg
TotalItems: 10
Notes: Giao hàng trước 5pm
CreatedBy: 1
CreatedAt: 2024-11-21 10:30:00
```

**Quan hệ**:
- 1 Order thuộc về 1 Layout (1-1)
- 1 Order được tạo bởi 1 User (N-1)

---

## Quy trình lưu dữ liệu

### Khi người dùng lưu đơn hàng:

```
1. Người dùng import Excel và xếp hàng
   ↓
2. Click "Lưu hàng hóa" và nhập tên đơn hàng
   ↓
3. Hệ thống tạo Layout:
   - Lưu thông tin container được sử dụng
   - Tính toán FillRate
   - Đếm TotalCargos
   ↓
4. Hệ thống lưu từng Cargo:
   - Lưu kích thước (Width, Height, Depth)
   - Lưu vị trí (PositionX, Y, Z)
   - Lưu góc xoay (RotationX, Y, Z)
   - Lưu màu sắc, nhãn, trọng lượng
   ↓
5. Hệ thống tạo Order:
   - Tạo OrderNumber tự động
   - Lưu CustomerName (tên đơn hàng)
   - Liên kết với LayoutId
   - Tính TotalWeight và TotalItems
   ↓
6. Hiển thị đơn hàng trong danh sách
```

---

## Truy vấn dữ liệu

### Lấy đơn hàng với đầy đủ thông tin:

```sql
SELECT 
    o.Id,
    o.OrderNumber,
    o.CustomerName,
    o.Status,
    o.TotalWeight,
    o.TotalItems,
    l.Name AS LayoutName,
    l.FillRate,
    c.Name AS ContainerName,
    c.Type AS ContainerType,
    u.FullName AS CreatedByName
FROM Orders o
INNER JOIN Layouts l ON o.LayoutId = l.Id
INNER JOIN Containers c ON l.ContainerId = c.Id
INNER JOIN Users u ON o.CreatedBy = u.Id
WHERE o.Id = 1
```

### Lấy tất cả kiện hàng của đơn hàng:

```sql
SELECT 
    cg.Id,
    cg.Width,
    cg.Height,
    cg.Depth,
    cg.PositionX,
    cg.PositionY,
    cg.PositionZ,
    cg.RotationX,
    cg.RotationY,
    cg.RotationZ,
    cg.Color,
    cg.Label,
    cg.Weight
FROM Orders o
INNER JOIN Layouts l ON o.LayoutId = l.Id
INNER JOIN Cargos cg ON cg.LayoutId = l.Id
WHERE o.Id = 1
ORDER BY cg.Id
```

### Tính thống kê:

```sql
-- Tổng thể tích đã sử dụng
SELECT 
    o.OrderNumber,
    SUM(cg.Width * cg.Height * cg.Depth) AS TotalVolume,
    l.FillRate
FROM Orders o
INNER JOIN Layouts l ON o.LayoutId = l.Id
INNER JOIN Cargos cg ON cg.LayoutId = l.Id
WHERE o.Id = 1
GROUP BY o.OrderNumber, l.FillRate
```

---

## Indexes (Đề xuất)

```sql
-- Tăng tốc tìm kiếm đơn hàng
CREATE INDEX IX_Orders_OrderNumber ON Orders(OrderNumber)
CREATE INDEX IX_Orders_CreatedAt ON Orders(CreatedAt DESC)
CREATE INDEX IX_Orders_Status ON Orders(Status)

-- Tăng tốc join
CREATE INDEX IX_Orders_LayoutId ON Orders(LayoutId)
CREATE INDEX IX_Layouts_ContainerId ON Layouts(ContainerId)
CREATE INDEX IX_Cargos_LayoutId ON Cargos(LayoutId)

-- Tăng tốc authentication
CREATE INDEX IX_Users_Username ON Users(Username)
CREATE INDEX IX_Users_Email ON Users(Email)
```

---

## Dung lượng ước tính

### Ví dụ với 1000 đơn hàng:

```
Users: 100 users × 1KB = 100KB
Containers: 10 containers × 1KB = 10KB
Layouts: 1000 layouts × 1KB = 1MB
Cargos: 1000 layouts × 50 cargos × 0.5KB = 25MB
Orders: 1000 orders × 2KB = 2MB

Tổng: ~28MB
```

### Với 10,000 đơn hàng:

```
Tổng: ~280MB
```

---

## Backup và Maintenance

### Backup định kỳ:
```sql
-- Full backup hàng ngày
BACKUP DATABASE CargoLoadingDB 
TO DISK = 'D:\Backups\CargoLoadingDB_Full.bak'
WITH INIT, COMPRESSION

-- Transaction log backup mỗi giờ
BACKUP LOG CargoLoadingDB 
TO DISK = 'D:\Backups\CargoLoadingDB_Log.trn'
WITH COMPRESSION
```

### Dọn dẹp dữ liệu cũ:
```sql
-- Xóa đơn hàng đã hủy sau 6 tháng
DELETE FROM Orders 
WHERE Status = 'Cancelled' 
AND CreatedAt < DATEADD(MONTH, -6, GETDATE())
```

---

## Bảo mật

1. **Mã hóa mật khẩu**: Sử dụng BCrypt/PBKDF2
2. **SQL Injection**: Sử dụng Parameterized Queries
3. **Authorization**: Kiểm tra quyền trước khi truy cập dữ liệu
4. **Audit Log**: Ghi log các thao tác quan trọng

---

## Mở rộng trong tương lai

### Có thể thêm:

1. **OrderItems**: Nếu cần quản lý sản phẩm riêng biệt
2. **Shipments**: Quản lý vận chuyển
3. **Payments**: Quản lý thanh toán
4. **AuditLogs**: Lưu lịch sử thay đổi
5. **Files**: Lưu file đính kèm (hình ảnh, tài liệu)

---

## Tài liệu tham khảo

- Entity Framework Core: https://docs.microsoft.com/ef/core/
- SQL Server Best Practices: https://docs.microsoft.com/sql/
- Database Design Patterns: https://www.databaseanswers.org/
