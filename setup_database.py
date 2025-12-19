# UPDATE 19.12.2025
# Add a tbale named OrderDetails - detail_id, order_id, book_id, quantity, price_at_purchase
# Remodify the Orders table - order_id, customer_name, phone, address, total_amount, create_at


import sqlite3
from datetime import datetime, timedelta

# Hàm hỗ trợ format giờ cho SQLite
def get_time_ago(days=0, hours=0, minutes=0, seconds=0):
    # Lấy giờ hiện tại trừ đi khoảng thời gian mong muốn
    t = datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    # Format chuẩn SQLite: YYYY-MM-DD HH:MM:SS
    return t.strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    db_path = "bookstore.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS OrderDetails")
    cursor.execute("DROP TABLE IF EXISTS Orders")
    cursor.execute("DROP TABLE IF EXISTS Books")


    # 2. Tạo bảng Books
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

    # 3. Tạo bảng Orders (Có create_at)
    cursor.execute('''
    CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        status TEXT,
        total_amount REAL,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE OrderDetails (
            detail_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            book_id INTEGER,
            quantity INTEGER,
            price_at_purchase REAL,
            FOREIGN KEY (order_id) REFERENCES Orders(order_id),
            FOREIGN KEY (book_id) REFERENCES Books(book_id)
                   )
''')

    # 4. Data Sách (Giữ nguyên)
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

    cursor.execute("INSERT INTO Orders (order_id, customer_name, phone, address, total_amount, status, create_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (1, "Nguyễn Văn A", "0912345678", "Hà Nội", 240000, "received", get_time_ago(days=5)))
    # Chi tiết đơn 1: Mua 2 cuốn Đắc nhân tâm (book_id=4, price=120000)
    cursor.execute("INSERT INTO OrderDetails (order_id, book_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", (1, 4, 2, 120000))

    # --- Đơn 2: Confirming (Quá hạn) -> Để test Timeout ---
    cursor.execute("INSERT INTO Orders (order_id, customer_name, phone, address, total_amount, status, create_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (2, "Hoàng Văn E", "0922223333", "Hà Nam", 240000, "confirming", get_time_ago(minutes=10)))
    cursor.execute("INSERT INTO OrderDetails (order_id, book_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)", (2, 10, 2, 120000))

    conn.commit()
    conn.close()
    print("✅ Đã khởi tạo Database chuẩn Relational (Orders & OrderDetails) thành công!")

if __name__ == "__main__":
    init_db()
