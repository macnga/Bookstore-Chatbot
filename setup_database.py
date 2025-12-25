# UPDATE 25.12.2025
#Add content into Books
# Add a tbale named OrderDetails - detail_id, order_id, book_id, quantity, price_at_purchase
# Remodify the Orders table - order_id, customer_name, phone, address, total_amount, status, create_at


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
        category TEXT,
        content TEXT
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
    # --- Dữ liệu cũ (1-30) ---
    (1, 'Lược sử thời gian', 'Stephen Hawking', 150000, 20, 'Khoa học', 'Khám phá các bí ẩn của vũ trụ từ Big Bang đến lỗ đen, giải thích vật lý thiên văn một cách dễ hiểu.'),
    (2, 'Nhà giả kim', 'Paulo Coelho', 80000, 50, 'Tiểu thuyết', 'Hành trình theo đuổi ước mơ của chàng chăn cừu Santiago, truyền cảm hứng về việc lắng nghe trái tim mình.'),
    (3, 'Lập trình Python từ A đến Z', 'Nguyễn Văn A', 250000, 15, 'Lập trình', 'Hướng dẫn toàn diện ngôn ngữ Python từ cơ bản đến nâng cao, phù hợp cho người mới bắt đầu.'),
    (4, 'Đắc nhân tâm', 'Dale Carnegie', 120000, 100, 'Kỹ năng sống', 'Nghệ thuật thu phục lòng người, cải thiện các mối quan hệ và đạt được thành công trong giao tiếp.'),
    (5, 'Trí tuệ nhân tạo', 'Nguyễn Xuân B', 300000, 5, 'Lập trình', 'Tổng quan về AI, từ lý thuyết cơ bản đến các ứng dụng thực tế trong công nghệ hiện đại.'),
    (6, 'Tư duy nhanh và chậm', 'Daniel Kahneman', 200000, 40, 'Tâm lý', 'Phân tích hai hệ thống tư duy chi phối nhận thức: một nhanh cảm tính và một chậm lý trí.'),
    (7, 'Khởi nghiệp tinh gọn', 'Eric Ries', 180000, 25, 'Kinh doanh', 'Phương pháp khởi nghiệp tập trung vào phát triển sản phẩm nhanh, kiểm chứng thị trường và điều chỉnh liên tục.'),
    (8, 'Thế giới phẳng', 'Thomas L. Friedman', 220000, 30, 'Kinh tế', 'Phân tích quá trình toàn cầu hóa thế kỷ 21, nơi công nghệ đã xóa bỏ các rào cản địa lý.'),
    (9, 'Dune', 'Frank Herbert', 170000, 35, 'Tiểu thuyết', 'Kiệt tác viễn tưởng về cuộc chiến giành quyền lực và tài nguyên trên hành tinh sa mạc Arrakis.'),
    (10, 'Harry Potter và Hòn đá phù thủy', 'J.K. Rowling', 120000, 60, 'Thiếu nhi', 'Khởi đầu hành trình của cậu bé phù thủy Harry Potter tại trường Hogwarts và cuộc đối đầu thế lực hắc ám.'),
    (11, 'Harry Potter và Phòng chứa bí mật', 'J.K. Rowling', 130000, 55, 'Thiếu nhi', 'Harry khám phá những bí ẩn đen tối tại Hogwarts liên quan đến người thừa kế của Slytherin.'),
    (12, 'Harry Potter và Tên tù nhân ngục Azkaban', 'J.K. Rowling', 140000, 50, 'Thiếu nhi', 'Harry đối mặt với quá khứ và sự thật về cha đỡ đầu Sirius Black, kẻ vượt ngục khét tiếng.'),
    (13, 'Lập trình C cơ bản', 'Nguyễn Văn C', 180000, 20, 'Lập trình', 'Tài liệu nhập môn ngôn ngữ C, trang bị nền tảng vững chắc về cú pháp và tư duy lập trình.'),
    (14, 'Clean Code', 'Robert C. Martin', 280000, 10, 'Lập trình', 'Các nguyên tắc và thực hành để viết mã nguồn sạch, dễ đọc, dễ bảo trì và tối ưu hóa.'),
    (15, 'Thiết kế giải thuật', 'Nguyễn Văn D', 260000, 15, 'Lập trình', 'Trình bày các phương pháp thiết kế và phân tích thuật toán để giải quyết bài toán tin học phức tạp.'),
    (16, 'Giải tích 1', 'Ngô Bảo Châu', 200000, 30, 'Giáo trình', 'Giáo trình toán đại cương chuyên sâu về giới hạn, đạo hàm và tích phân.'),
    (17, 'Đại số tuyến tính', 'Nguyễn Văn E', 190000, 25, 'Giáo trình', 'Cung cấp kiến thức về ma trận, không gian vector, ứng dụng trong khoa học dữ liệu và đồ họa.'),
    (18, 'Machine Learning cơ bản', 'Andrew Ng', 320000, 10, 'Khoa học', 'Giới thiệu các thuật toán học máy phổ biến như hồi quy, phân loại kèm ví dụ thực hành.'),
    (19, 'Deep Learning', 'Ian Goodfellow', 450000, 8, 'Khoa học', 'Tài liệu chuyên sâu về học sâu, mạng nơ-ron và ứng dụng trong xử lý ảnh, ngôn ngữ tự nhiên.'),
    (20, 'Blockchain cơ bản', 'Satoshi Nakamoto', 210000, 12, 'Công nghệ', 'Giải thích cơ chế hoạt động của chuỗi khối, tiền mã hóa và ứng dụng tài chính phi tập trung.'),
    (21, 'Khuyến học', 'Fukuzawa Yukichi', 110000, 40, 'Kỹ năng sống', 'Tác phẩm kinh điển nhấn mạnh tầm quan trọng của việc học và tư duy độc lập đối với quốc gia.'),
    (22, '7 thói quen để thành đạt', 'Stephen R. Covey', 150000, 45, 'Kỹ năng sống', 'Chia sẻ những thói quen cốt lõi giúp thay đổi tư duy, nâng cao hiệu suất và cân bằng cuộc sống.'),
    (23, 'Tuổi trẻ đáng giá bao nhiêu', 'Rosie Nguyễn', 100000, 30, 'Kỹ năng sống', 'Những bài học cho người trẻ về việc tự học, trải nghiệm và định hướng tương lai.'),
    (24, 'Muôn kiếp nhân sinh', 'Nguyên Phong', 160000, 35, 'Tâm linh', 'Khám phá quy luật nhân quả và luân hồi qua những câu chuyện kỳ lạ về kiếp sống.'),
    (25, 'Homo Deus', 'Yuval Noah Harari', 240000, 20, 'Khoa học', 'Dự báo tương lai loài người trong kỷ nguyên công nghệ, vươn tới sự bất tử và hạnh phúc.'),
    (26, 'Sapiens: Lược sử loài người', 'Yuval Noah Harari', 230000, 25, 'Khoa học', 'Lược sử toàn diện về sự hình thành và phát triển của loài người từ tiền sử đến hiện đại.'),
    (27, 'Sherlock Holmes: Toàn tập', 'Arthur Conan Doyle', 300000, 15, 'Trinh thám', 'Tuyển tập những vụ án ly kỳ và tài suy luận logic siêu phàm của vị thám tử lừng danh.'),
    (28, 'Thám tử lừng danh Conan', 'Aoyama Gosho', 90000, 100, 'Truyện tranh', 'Truyện tranh về cậu thám tử trung học bị thu nhỏ, chuyên phá giải các vụ án hóc búa.'),
    (29, 'One Piece', 'Eiichiro Oda', 95000, 100, 'Truyện tranh', 'Hành trình phiêu lưu của Luffy và đồng đội trên đại dương để tìm kiếm kho báu huyền thoại.'),
    (30, 'Naruto', 'Masashi Kishimoto', 95000, 100, 'Truyện tranh', 'Câu chuyện về nỗ lực của một ninja trẻ tuổi bị xa lánh trên con đường trở thành người lãnh đạo.'),

    # --- Dữ liệu mới bổ sung (31-100) ---
    # Văn học Việt Nam & Kinh điển
    (31, 'Số đỏ', 'Vũ Trọng Phụng', 95000, 40, 'Văn học VN', 'Tiểu thuyết trào phúng kinh điển phê phán thói giả dối và sự lố lăng của xã hội thượng lưu xưa.'),
    (32, 'Dế Mèn phiêu lưu ký', 'Tô Hoài', 70000, 80, 'Thiếu nhi', 'Câu chuyện phiêu lưu của chú Dế Mèn, bài học về tình bạn và lòng nhân ái cho trẻ em.'),
    (33, 'Mắt biếc', 'Nguyễn Nhật Ánh', 110000, 60, 'Tiểu thuyết', 'Câu chuyện tình đơn phương buồn bã và đẹp đẽ của Ngạn dành cho Hà Lan qua bao thăng trầm.'),
    (34, 'Đất rừng phương Nam', 'Đoàn Giỏi', 85000, 50, 'Văn học VN', 'Bức tranh thiên nhiên và con người Nam Bộ hào sảng qua cuộc đời lưu lạc của cậu bé An.'),
    (35, 'Vợ nhặt', 'Kim Lân', 50000, 30, 'Văn học VN', 'Truyện ngắn xuất sắc về tình người và khát vọng sống mãnh liệt trong nạn đói năm 1945.'),
    (36, 'Cho tôi xin một vé đi tuổi thơ', 'Nguyễn Nhật Ánh', 90000, 70, 'Tiểu thuyết', 'Tấm vé tàu đưa người đọc trở về những ký ức ngây ngô và trong trẻo của thời thơ ấu.'),
    (37, 'Tắt đèn', 'Ngô Tất Tố', 60000, 35, 'Văn học VN', 'Bức tranh hiện thực tăm tối của nông thôn Việt Nam và số phận bi thảm của chị Dậu.'),
    (38, 'Chiếc thuyền ngoài xa', 'Nguyễn Minh Châu', 55000, 25, 'Văn học VN', 'Suy ngẫm sâu sắc về mối quan hệ giữa nghệ thuật và cuộc đời qua câu chuyện gia đình làng chài.'),
    (39, 'Rừng Na Uy', 'Haruki Murakami', 160000, 45, 'Tiểu thuyết', 'Câu chuyện ám ảnh về tình yêu, sự mất mát và trưởng thành trong bối cảnh nước Nhật thập niên 60.'),
    (40, 'Bố già (The Godfather)', 'Mario Puzo', 180000, 50, 'Tiểu thuyết', 'Kiệt tác về thế giới ngầm Mafia, danh dự gia đình và quyền lực của ông trùm Don Vito Corleone.'),

    # Văn học nước ngoài kinh điển
    (41, 'Ông già và biển cả', 'Ernest Hemingway', 75000, 40, 'Tiểu thuyết', 'Cuộc chiến kiên cường của ông lão đánh cá với con cá kiếm khổng lồ, biểu tượng cho nghị lực con người.'),
    (42, 'Giết con chim nhại', 'Harper Lee', 135000, 55, 'Tiểu thuyết', 'Câu chuyện cảm động về lòng dũng cảm và chống lại nạn phân biệt chủng tộc qua ánh mắt trẻ thơ.'),
    (43, 'Gatsby vĩ đại', 'F. Scott Fitzgerald', 115000, 30, 'Tiểu thuyết', 'Bức tranh hào nhoáng nhưng phù phiếm của Giấc mơ Mỹ và bi kịch tình yêu của Jay Gatsby.'),
    (44, 'Trăm năm cô đơn', 'Gabriel Garcia Marquez', 190000, 20, 'Tiểu thuyết', 'Sử thi huyền ảo về dòng họ Buendía và ngôi làng Macondo, phản ánh lịch sử Mỹ Latinh.'),
    (45, 'Kiêu hãnh và định kiến', 'Jane Austen', 125000, 45, 'Tiểu thuyết', 'Câu chuyện tình lãng mạn và châm biếm sâu sắc về tầng lớp quý tộc Anh thế kỷ 19.'),
    (46, 'Tội ác và hình phạt', 'Fyodor Dostoevsky', 220000, 15, 'Tiểu thuyết', 'Phân tích tâm lý tội phạm sâu sắc qua dằn vặt của Raskolnikov sau khi phạm tội giết người.'),
    (47, 'Hai số phận', 'Jeffrey Archer', 175000, 35, 'Tiểu thuyết', 'Cuộc đời song hành đầy kịch tính của hai người đàn ông sinh cùng ngày nhưng khác biệt hoàn toàn về xuất thân.'),
    (48, 'Hoàng tử bé', 'Antoine de Saint-Exupéry', 65000, 90, 'Thiếu nhi', 'Câu chuyện ngụ ngôn triết học nhẹ nhàng về tình yêu và ý nghĩa cuộc sống dành cho cả người lớn.'),
    (49, 'Tiếng chim hót trong bụi mận gai', 'Colleen McCullough', 210000, 25, 'Tiểu thuyết', 'Bản tình ca bi tráng kéo dài ba thế hệ của gia đình Cleary trên vùng đất Úc hoang dã.'),
    (50, 'Những người khốn khổ', 'Victor Hugo', 350000, 10, 'Tiểu thuyết', 'Bức tranh xã hội Pháp thế kỷ 19, ca ngợi tình yêu thương và lòng nhân ái qua nhân vật Jean Valjean.'),

    # Công nghệ & Lập trình nâng cao
    (51, 'The Pragmatic Programmer', 'Andy Hunt', 320000, 15, 'Lập trình', 'Những lời khuyên thực tế giúp lập trình viên trở nên chuyên nghiệp và hiệu quả hơn trong công việc.'),
    (52, 'Introduction to Algorithms', 'Thomas H. Cormen', 550000, 5, 'Lập trình', 'Kinh thánh về thuật toán, cung cấp phân tích sâu sắc về nhiều loại thuật toán và cấu trúc dữ liệu.'),
    (53, 'Design Patterns', 'Erich Gamma', 280000, 12, 'Lập trình', 'Giới thiệu 23 mẫu thiết kế phần mềm kinh điển giúp giải quyết các vấn đề kiến trúc phổ biến.'),
    (54, 'Refactoring', 'Martin Fowler', 300000, 10, 'Lập trình', 'Kỹ thuật cải thiện thiết kế của mã nguồn hiện có mà không làm thay đổi hành vi bên ngoài.'),
    (55, 'Head First Design Patterns', 'Eric Freeman', 340000, 18, 'Lập trình', 'Cách tiếp cận trực quan và vui nhộn để học các mẫu thiết kế, giúp não bộ ghi nhớ lâu hơn.'),
    (56, 'You Don\'t Know JS', 'Kyle Simpson', 180000, 25, 'Lập trình', 'Bộ sách đi sâu vào các cơ chế cốt lõi và phức tạp của ngôn ngữ JavaScript.'),
    (57, 'Grokking Algorithms', 'Aditya Bhargava', 190000, 30, 'Lập trình', 'Hướng dẫn thuật toán bằng hình ảnh minh họa dễ hiểu, phù hợp cho người mới bắt đầu hoặc ôn tập.'),
    (58, 'Cracking the Coding Interview', 'Gayle Laakmann', 380000, 20, 'Lập trình', 'Cẩm nang luyện phỏng vấn xin việc tại các công ty công nghệ lớn với hàng trăm bài tập code.'),
    (59, 'Docker & Kubernetes cơ bản', 'Nguyễn Văn F', 220000, 25, 'Công nghệ', 'Hướng dẫn triển khai ứng dụng container hóa và quản lý hệ thống phân tán hiện đại.'),
    (60, 'Bảo mật thông tin', 'Nguyễn Văn G', 240000, 15, 'Công nghệ', 'Kiến thức nền tảng về an toàn thông tin, mã hóa và phòng chống tấn công mạng.'),

    # Kinh tế & Quản trị
    (61, 'Cha giàu cha nghèo', 'Robert Kiyosaki', 110000, 60, 'Kinh tế', 'Thay đổi tư duy về tiền bạc, tài sản và tiêu sản để đạt được tự do tài chính.'),
    (62, 'Từ tốt đến vĩ đại', 'Jim Collins', 165000, 30, 'Kinh doanh', 'Nghiên cứu về những yếu tố then chốt giúp các công ty nhảy vọt từ mức trung bình lên vĩ đại.'),
    (63, 'Chiến tranh tiền tệ', 'Song Hongbing', 195000, 20, 'Kinh tế', 'Góc nhìn khác biệt về lịch sử tài chính thế giới và những âm mưu đằng sau các cuộc khủng hoảng.'),
    (64, 'Marketing giỏi phải kiếm được tiền', 'Sergio Zyman', 140000, 35, 'Kinh doanh', 'Tư duy marketing thực chiến, tập trung vào hiệu quả doanh số thay vì chỉ xây dựng thương hiệu.'),
    (65, 'Dạy con làm giàu', 'Robert Kiyosaki', 120000, 50, 'Kỹ năng sống', 'Bộ sách hướng dẫn các bậc phụ huynh giáo dục tài chính cho con cái từ sớm.'),
    (66, 'Phi lý trí', 'Dan Ariely', 155000, 40, 'Tâm lý', 'Khám phá những động lực ẩn giấu khiến con người đưa ra các quyết định phi logic.'),
    (67, 'Thiên nga đen', 'Nassim Nicholas Taleb', 210000, 15, 'Kinh tế', 'Tác động to lớn của những sự kiện hiếm gặp và khó lường đối với nền kinh tế và lịch sử.'),
    (68, 'Tỷ phú bán giày', 'Tony Hsieh', 130000, 30, 'Kinh doanh', 'Câu chuyện thành công của Zappos và triết lý xây dựng văn hóa doanh nghiệp hạnh phúc.'),
    (69, 'Elon Musk', 'Walter Isaacson', 280000, 25, 'Tiểu sử', 'Tiểu sử chi tiết về cuộc đời, tầm nhìn và tính cách điên rồ của tỷ phú công nghệ Elon Musk.'),
    (70, 'Steve Jobs', 'Walter Isaacson', 260000, 25, 'Tiểu sử', 'Cuốn tiểu sử chính thức về người sáng lập Apple, thiên tài sáng tạo và nhà lãnh đạo khắc nghiệt.'),

    # Lịch sử, Khoa học & Xã hội
    (71, 'Súng, Vi trùng và Thép', 'Jared Diamond', 230000, 15, 'Khoa học', 'Giải thích sự phát triển không đồng đều giữa các nền văn minh qua các yếu tố địa lý và sinh học.'),
    (72, 'Vũ trụ (Cosmos)', 'Carl Sagan', 250000, 20, 'Khoa học', 'Hành trình khám phá không gian và vị trí của loài người trong vũ trụ bao la.'),
    (73, 'Tâm lý học đám đông', 'Gustave Le Bon', 100000, 30, 'Tâm lý', 'Nghiên cứu kinh điển về đặc điểm và hành vi của con người khi ở trong một tập thể.'),
    (74, 'Những tù nhân của địa lý', 'Tim Marshall', 185000, 25, 'Chính trị', 'Bản đồ địa chính trị thế giới và cách địa lý chi phối các quyết định của các quốc gia.'),
    (75, 'Gen: Lịch sử và tương lai', 'Siddhartha Mukherjee', 290000, 10, 'Khoa học', 'Lịch sử khám phá gen di truyền và những tác động đạo đức của công nghệ sinh học.'),
    (76, 'Lược sử tương lai', 'Yuval Noah Harari', 240000, 20, 'Khoa học', 'Tiếp nối Sapiens, bàn về những thách thức và vận mệnh của loài người trong thế kỷ 21.'),
    (77, 'Tại sao chúng ta ngủ', 'Matthew Walker', 210000, 30, 'Sức khỏe', 'Khám phá khoa học về giấc ngủ và tầm quan trọng sống còn của nó đối với sức khỏe.'),
    (78, 'Cơ thể 4 giờ', 'Tim Ferriss', 190000, 20, 'Sức khỏe', 'Các phương pháp "hack" cơ thể để giảm mỡ, tăng cơ và cải thiện sức khỏe với nỗ lực tối thiểu.'),
    (79, 'Lời hứa về một cây bút chì', 'Adam Braun', 110000, 35, 'Kỹ năng sống', 'Hành trình từ một chàng trai trẻ đến người sáng lập tổ chức từ thiện xây trường học trên toàn cầu.'),
    (80, 'Suối nguồn', 'Ayn Rand', 270000, 12, 'Tiểu thuyết', 'Tác phẩm triết học tôn vinh chủ nghĩa cá nhân và sự sáng tạo qua hình tượng kiến trúc sư Howard Roark.'),

    # Manga & Truyện tranh
    (81, 'Dragon Ball (7 viên ngọc rồng)', 'Akira Toriyama', 25000, 200, 'Truyện tranh', 'Hành trình tìm ngọc rồng và bảo vệ trái đất của Goku cùng những người bạn.'),
    (82, 'Doraemon', 'Fujiko F. Fujio', 20000, 300, 'Truyện tranh', 'Chú mèo máy đến từ tương lai với những bảo bối thần kỳ giúp đỡ cậu bé Nobita hậu đậu.'),
    (83, 'Spy x Family', 'Tatsuya Endo', 45000, 100, 'Truyện tranh', 'Câu chuyện hài hước về một gia đình điệp viên chắp vá gồm bố điệp viên, mẹ sát thủ và con gái ngoại cảm.'),
    (84, 'Attack on Titan', 'Hajime Isayama', 50000, 80, 'Truyện tranh', 'Cuộc chiến sinh tồn tàn khốc của loài người chống lại những gã khổng lồ ăn thịt người.'),
    (85, 'Demon Slayer (Thanh gươm diệt quỷ)', 'Koyoharu Gotouge', 40000, 120, 'Truyện tranh', 'Tanjiro gia nhập Sát Quỷ Đội để tìm cách cứu em gái bị hóa thành quỷ.'),
    (86, 'Jujutsu Kaisen (Chú thuật hồi chiến)', 'Gege Akutami', 45000, 90, 'Truyện tranh', 'Cuộc chiến giữa các chú thuật sư và những lời nguyền nguy hiểm đe dọa con người.'),
    (87, 'Chainsaw Man', 'Tatsuki Fujimoto', 50000, 70, 'Truyện tranh', 'Câu chuyện điên rồ và bạo lực về Denji, người có khả năng biến thành quỷ cưa.'),
    (88, 'Black Jack', 'Osamu Tezuka', 35000, 60, 'Truyện tranh', 'Bác sĩ quái dị với tài năng phẫu thuật thần sầu, chuyên chữa những ca bệnh nan y.'),
    (89, 'Shin - Cậu bé bút chì', 'Yoshito Usui', 25000, 150, 'Truyện tranh', 'Những câu chuyện đời thường hài hước và "khó đỡ" của cậu bé 5 tuổi Shin-chan.'),
    (90, 'Your Name (Light Novel)', 'Makoto Shinkai', 60000, 80, 'Tiểu thuyết', 'Câu chuyện kỳ diệu về sự hoán đổi thân xác giữa hai bạn trẻ và nỗ lực tìm kiếm nhau qua không gian.'),

    # Kỹ năng, Ngoại ngữ & Sống đẹp
    (91, 'Hack não 1500 từ tiếng Anh', 'Nguyễn Văn Hiệp', 290000, 40, 'Ngoại ngữ', 'Phương pháp học từ vựng tiếng Anh qua âm thanh tương tự và truyện chêm thú vị.'),
    (92, 'Ngữ pháp tiếng Anh Mai Lan Hương', 'Mai Lan Hương', 80000, 100, 'Ngoại ngữ', 'Sách bài tập ngữ pháp kinh điển dành cho học sinh Việt Nam ôn luyện tiếng Anh.'),
    (93, 'Ăn gì không chết', 'Michael Greger', 250000, 25, 'Sức khỏe', 'Khoa học về dinh dưỡng thực vật giúp ngăn ngừa và đảo ngược các bệnh mãn tính.'),
    (94, 'Nhân tố Enzyme', 'Hiromi Shinya', 115000, 50, 'Sức khỏe', 'Phương pháp sống lành mạnh và ăn uống để duy trì lượng enzyme diệu kỳ trong cơ thể.'),
    (95, 'Lối sống tối giản của người Nhật', 'Sasaki Fumio', 105000, 45, 'Kỹ năng sống', 'Hướng dẫn vứt bỏ đồ đạc dư thừa để tìm lại sự bình yên và hạnh phúc trong tâm hồn.'),
    (96, 'Chủ nghĩa khắc kỷ', 'William B. Irvine', 145000, 30, 'Triết học', 'Áp dụng triết lý cổ đại vào đời sống hiện đại để rèn luyện sự bình thản trước biến cố.'),
    (97, 'Đừng lựa chọn an nhàn khi còn trẻ', 'Cảnh Thiên', 95000, 60, 'Kỹ năng sống', 'Lời khuyên cho giới trẻ về sự nỗ lực, phấn đấu không ngừng nghỉ để gặt hái thành công.'),
    (98, 'Bạn đắt giá bao nhiêu', 'Vãn Tình', 100000, 70, 'Kỹ năng sống', 'Góc nhìn sắc sảo về tình yêu, hôn nhân và giá trị bản thân của phụ nữ hiện đại.'),
    (99, 'Khéo ăn nói sẽ có được thiên hạ', 'Trác Nhã', 110000, 80, 'Kỹ năng sống', 'Nghệ thuật giao tiếp ứng xử khéo léo giúp mở rộng mối quan hệ và thăng tiến.'),
    (100, 'Hành trình về phương Đông', 'Blair T. Spalding', 125000, 55, 'Tâm linh', 'Cuộc hành trình khám phá những giá trị tâm linh huyền bí của Ấn Độ và phương Đông.')
]
    cursor.executemany("INSERT INTO Books VALUES (?, ?, ?, ?, ?, ?, ?)", books_data)

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
