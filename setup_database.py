import sqlite3

# Kết nối DB
conn = sqlite3.connect("bookstore.db")
cursor = conn.cursor()

# Xoá bảng cũ
cursor.execute("DROP TABLE IF EXISTS Books")
cursor.execute("DROP TABLE IF EXISTS Orders")

# Tạo bảng Books
cursor.execute('''
CREATE TABLE Books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    category TEXT
)
''')

# Tạo bảng Orders
cursor.execute('''
CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    book_id INTEGER,
    quantity INTEGER,
    status TEXT,
    FOREIGN KEY (book_id) REFERENCES Books (book_id)
)
''')

# 30 sách mẫu
books_data = [
    (1, 'Lược sử thời gian', 'Stephen Hawking', 150000, 20, 'Khoa học'),
    (2, 'Nhà giả kim', 'Paulo Coelho', 80000, 50, 'Tiểu thuyết'),
    (3, 'Lập trình Python từ A đến Z', 'Nguyễn Văn A', 250000, 15, 'Lập trình'),
    (4, 'Đắc nhân tâm', 'Dale Carnegie', 120000, 100, 'Kỹ năng sống'),
    (5, 'Trí tuệ nhân tạo', 'Nguyễn Xuân B', 300000, 5, 'Lập trình'),
    (6, 'Tư duy nhanh và chậm', 'Daniel Kahneman', 200000, 40, 'Tâm lý'),
    (7, 'Khởi nghiệp tinh gọn', 'Eric Ries', 180000, 25, 'Kinh doanh'),
    (8, 'Thế giới phẳng', 'Thomas L. Friedman', 220000, 30, 'Kinh tế'),
    (9, 'Dune', 'Frank Herbert', 170000, 35, 'Tiểu thuyết'),
    (10, 'Harry Potter và Hòn đá phù thủy', 'J.K. Rowling', 120000, 60, 'Thiếu nhi'),
    (11, 'Harry Potter và Phòng chứa bí mật', 'J.K. Rowling', 130000, 55, 'Thiếu nhi'),
    (12, 'Harry Potter và Tên tù nhân ngục Azkaban', 'J.K. Rowling', 140000, 50, 'Thiếu nhi'),
    (13, 'Lập trình C cơ bản', 'Nguyễn Văn C', 180000, 20, 'Lập trình'),
    (14, 'Clean Code', 'Robert C. Martin', 280000, 10, 'Lập trình'),
    (15, 'Thiết kế giải thuật', 'Nguyễn Văn D', 260000, 15, 'Lập trình'),
    (16, 'Giải tích 1', 'Ngô Bảo Châu', 200000, 30, 'Giáo trình'),
    (17, 'Đại số tuyến tính', 'Nguyễn Văn E', 190000, 25, 'Giáo trình'),
    (18, 'Machine Learning cơ bản', 'Andrew Ng', 320000, 10, 'Khoa học'),
    (19, 'Deep Learning', 'Ian Goodfellow', 450000, 8, 'Khoa học'),
    (20, 'Blockchain cơ bản', 'Satoshi Nakamoto', 210000, 12, 'Công nghệ'),
    (21, 'Khuyến học', 'Fukuzawa Yukichi', 110000, 40, 'Kỹ năng sống'),
    (22, '7 thói quen để thành đạt', 'Stephen R. Covey', 150000, 45, 'Kỹ năng sống'),
    (23, 'Tuổi trẻ đáng giá bao nhiêu', 'Rosie Nguyễn', 100000, 30, 'Kỹ năng sống'),
    (24, 'Muôn kiếp nhân sinh', 'Nguyên Phong', 160000, 35, 'Tâm linh'),
    (25, 'Homo Deus', 'Yuval Noah Harari', 240000, 20, 'Khoa học'),
    (26, 'Sapiens: Lược sử loài người', 'Yuval Noah Harari', 230000, 25, 'Khoa học'),
    (27, 'Sherlock Holmes: Toàn tập', 'Arthur Conan Doyle', 300000, 15, 'Trinh thám'),
    (28, 'Thám tử lừng danh Conan', 'Aoyama Gosho', 90000, 100, 'Truyện tranh'),
    (29, 'One Piece', 'Eiichiro Oda', 95000, 100, 'Truyện tranh'),
    (30, 'Naruto', 'Masashi Kishimoto', 95000, 100, 'Truyện tranh')
]
cursor.executemany("INSERT INTO Books VALUES (?, ?, ?, ?, ?, ?)", books_data)

# 5 đơn hàng mẫu
orders_data = [
    (1, "Nguyễn Văn A", "0912345678", "Hà Nội", 4, 2, "Delivered"),   # 2 cuốn Đắc nhân tâm
    (2, "Trần Thị B", "0987654321", "Hải Phòng", 2, 1, "Shipped"),    # 1 cuốn Nhà giả kim
    (3, "Lê Văn C", "0933334444", "Đà Nẵng", 14, 1, "Pending"),       # 1 cuốn Clean Code
    (4, "Phạm Thị D", "0977778888", "Hồ Chí Minh", 25, 3, "Delivered"), # 3 cuốn Homo Deus
    (5, "Hoàng Văn E", "0922223333", "Cần Thơ", 10, 2, "Pending"),    # 2 cuốn Harry Potter 1
]
cursor.executemany(
    "INSERT INTO Orders (order_id, customer_name, phone, address, book_id, quantity, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
    orders_data
)

conn.commit()
conn.close()

print("Cơ sở dữ liệu đã được tạo với 30 sách và 5 đơn hàng mẫu thành công!")
