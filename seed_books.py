#Version 29.12.2025
# Sử dụng để thêm dữ liệu Books cho DB

import sqlite3
import config

# Dữ liệu bổ sung (101-300)
more_books_data = [
    # --- Trinh thám & Bí ẩn (Keigo, Dan Brown,...) ---
    (101, 'Phía sau nghi can X', 'Keigo Higashino', 135000, 40, 'Trinh thám', 'Cuộc đấu trí đỉnh cao giữa một thiên tài toán học muốn che giấu tội ác và một nhà vật lý học thiên tài.'),
    (102, 'Bạch dạ hành', 'Keigo Higashino', 180000, 30, 'Trinh thám', 'Câu chuyện ám ảnh về hai đứa trẻ lớn lên dưới bóng đen của tội ác và mối quan hệ kỳ lạ giữa chúng.'),
    (103, 'Điều kỳ diệu của tiệm tạp hóa Namiya', 'Keigo Higashino', 110000, 80, 'Văn học', 'Một tiệm tạp hóa cũ kỹ nối liền quá khứ và hiện tại qua những lá thư tư vấn đầy cảm động.'),
    (104, 'Hỏa ngục (Inferno)', 'Dan Brown', 190000, 35, 'Trinh thám', 'Robert Langdon chạy đua với thời gian để ngăn chặn một đại dịch toàn cầu được mã hóa trong tác phẩm của Dante.'),
    (105, 'Biểu tượng thất truyền', 'Dan Brown', 210000, 25, 'Trinh thám', 'Khám phá những bí mật của Hội Tam Điểm tại Washington D.C. qua cuộc phiêu lưu nghẹt thở.'),
    (106, 'Sự im lặng của bầy cừu', 'Thomas Harris', 140000, 45, 'Trinh thám', 'Cuộc đối đầu tâm lý giữa nữ thực tập sinh FBI Clarice Starling và kẻ ăn thịt người Hannibal Lecter.'),
    (107, 'Cô gái có hình xăm rồng', 'Stieg Larsson', 160000, 30, 'Trinh thám', 'Vụ án mất tích bí ẩn kéo dài 40 năm được điều tra bởi một nhà báo và một nữ hacker thiên tài.'),
    (108, 'Mười tội ác (Tập 1)', 'Tri Thù', 125000, 50, 'Trinh thám', 'Tuyển tập 10 vụ án kinh hoàng có thật trong lịch sử Trung Quốc được tiểu thuyết hóa.'),
    (109, 'Đề thi đẫm máu', 'Lôi Mễ', 145000, 40, 'Trinh thám', 'Cuộc chiến chống lại tên sát nhân biến thái chuyên ra đề thi bằng máu cho cảnh sát Phương Mộc.'),
    (110, 'Sherlock Holmes: Chiếc nhẫn tình cờ', 'Arthur Conan Doyle', 85000, 60, 'Trinh thám', 'Vụ án đầu tiên đưa Sherlock Holmes và bác sĩ Watson đến với nhau qua một vụ giết người bí ẩn.'),

    # --- Fantasy & Sci-Fi Kinh điển (Chúa Nhẫn, Hunger Games...) ---
    (111, 'Chúa tể những chiếc nhẫn: Đoàn hộ nhẫn', 'J.R.R. Tolkien', 250000, 20, 'Tiểu thuyết', 'Khởi đầu hành trình vĩ đại của Frodo và những người bạn để tiêu hủy chiếc nhẫn quyền lực.'),
    (112, 'Chúa tể những chiếc nhẫn: Hai tòa tháp', 'J.R.R. Tolkien', 250000, 20, 'Tiểu thuyết', 'Cuộc chiến mở rộng khi đoàn hộ nhẫn bị chia rẽ và thế lực bóng tối trỗi dậy mạnh mẽ.'),
    (113, 'Chúa tể những chiếc nhẫn: Nhà vua trở về', 'J.R.R. Tolkien', 250000, 20, 'Tiểu thuyết', 'Trận chiến cuối cùng quyết định vận mệnh Trung Địa và sự trở lại của người thừa kế ngai vàng.'),
    (114, 'Anh chàng Hobbit', 'J.R.R. Tolkien', 150000, 40, 'Tiểu thuyết', 'Cuộc phiêu lưu bất đắc dĩ của Bilbo Baggins cùng 13 chú lùn để giành lại kho báu từ rồng Smaug.'),
    (115, 'Đấu trường sinh tử (The Hunger Games)', 'Suzanne Collins', 130000, 55, 'Tiểu thuyết', 'Katniss Everdeen tình nguyện tham gia trò chơi sinh tử để cứu em gái trong một thế giới hậu tận thế.'),
    (116, 'Bắt lửa (Catching Fire)', 'Suzanne Collins', 130000, 50, 'Tiểu thuyết', 'Hậu quả của chiến thắng và mầm mống của cuộc nổi dậy chống lại Capitol bắt đầu nhen nhóm.'),
    (117, 'Húng nhại (Mockingjay)', 'Suzanne Collins', 140000, 45, 'Tiểu thuyết', 'Cuộc chiến toàn diện lật đổ Capitol và cái giá phải trả cho tự do.'),
    (118, 'Người truyền ký ức (The Giver)', 'Lois Lowry', 90000, 60, 'Tiểu thuyết', 'Một xã hội hoàn hảo không có đau khổ nhưng cũng không có cảm xúc và ký ức.'),
    (119, 'Fahrenheit 451 (451 độ F)', 'Ray Bradbury', 110000, 35, 'Tiểu thuyết', 'Một thế giới tương lai nơi sách bị cấm và lính cứu hỏa có nhiệm vụ đốt sách.'),
    (120, 'Chuyện người tùy nữ', 'Margaret Atwood', 155000, 30, 'Tiểu thuyết', 'Thế giới tăm tối nơi phụ nữ bị tước đoạt quyền con người và trở thành công cụ sinh sản.'),

    # --- Kinh tế, Quản trị & Start-up ---
    (121, 'Zero to One (Không đến Một)', 'Peter Thiel', 140000, 40, 'Kinh doanh', 'Cách xây dựng tương lai và tạo ra những công ty đột phá thay vì sao chép cái đã có.'),
    (122, 'Chiến lược đại dương xanh', 'W. Chan Kim', 180000, 30, 'Kinh doanh', 'Làm thế nào để tạo ra khoảng trống thị trường vô đối thủ và khiến cạnh tranh trở nên không cần thiết.'),
    (123, 'Nguyên lý 80/20', 'Richard Koch', 135000, 50, 'Kinh tế', 'Cách đạt được nhiều thành quả hơn với ít nỗ lực hơn bằng cách tập trung vào 20% quan trọng nhất.'),
    (124, 'Nghĩ giàu làm giàu', 'Napoleon Hill', 110000, 100, 'Kỹ năng sống', '13 nguyên tắc thành công được đúc kết từ việc nghiên cứu hàng trăm triệu phú Mỹ.'),
    (125, 'Tư duy nhanh và chậm', 'Daniel Kahneman', 220000, 25, 'Tâm lý', 'Khám phá hai hệ thống tư duy chi phối mọi quyết định và phán đoán của con người.'),
    (126, 'Cú hích (Nudge)', 'Richard Thaler', 160000, 30, 'Kinh tế', 'Cách những tác động nhỏ có thể cải thiện quyết định về sức khỏe, tài chính và hạnh phúc.'),
    (127, 'Điểm bùng phát', 'Malcolm Gladwell', 145000, 35, 'Kinh tế', 'Làm thế nào những điều nhỏ bé có thể tạo nên sự khác biệt to lớn và lan truyền như virus.'),
    (128, 'Những kẻ xuất chúng (Outliers)', 'Malcolm Gladwell', 145000, 40, 'Kỹ năng sống', 'Giải mã bí ẩn đằng sau thành công của những nhân vật kiệt xuất nhất thế giới.'),
    (129, 'Trong chớp mắt (Blink)', 'Malcolm Gladwell', 130000, 40, 'Tâm lý', 'Sức mạnh của việc suy nghĩ mà không cần suy nghĩ, và trực giác hoạt động như thế nào.'),
    (130, 'Dẫn đầu hay là chết', 'Grant Cardone', 190000, 20, 'Kinh doanh', 'Tư duy bán hàng quyết liệt và cách thống trị thị trường trong thời đại cạnh tranh khốc liệt.'),

    # --- Tâm lý học, Kỹ năng & Phát triển bản thân ---
    (131, 'Atomic Habits (Thay đổi tí hon)', 'James Clear', 185000, 60, 'Kỹ năng sống', 'Xây dựng thói quen tốt và phá bỏ thói quen xấu thông qua những thay đổi nhỏ mỗi ngày.'),
    (132, 'Deep Work (Làm việc sâu)', 'Cal Newport', 150000, 35, 'Kỹ năng sống', 'Kỹ năng tập trung cao độ trong một thế giới đầy rẫy sự xao nhãng để đạt hiệu suất tối đa.'),
    (133, 'Essentialism (Tối giản thông minh)', 'Greg McKeown', 140000, 40, 'Kỹ năng sống', 'Nghệ thuật theo đuổi ít hơn nhưng tốt hơn, tập trung vào điều thực sự quan trọng.'),
    (134, 'Mindset (Tâm lý học thành công)', 'Carol S. Dweck', 170000, 30, 'Tâm lý', 'Sự khác biệt giữa tư duy cố định và tư duy phát triển ảnh hưởng đến thành công như thế nào.'),
    (135, 'Sức mạnh của sự tĩnh lặng', 'Eckhart Tolle', 120000, 50, 'Tâm linh', 'Tìm kiếm sự bình an nội tại và sống trọn vẹn trong giây phút hiện tại.'),
    (136, 'Đàn ông sao Hỏa đàn bà sao Kim', 'John Gray', 160000, 55, 'Tâm lý', 'Cẩm nang kinh điển về thấu hiểu sự khác biệt tâm lý giữa nam và nữ trong tình yêu.'),
    (137, 'Ngôn ngữ cơ thể', 'Allan Pease', 130000, 45, 'Kỹ năng sống', 'Đọc vị suy nghĩ của người khác thông qua cử chỉ, điệu bộ và ánh mắt.'),
    (138, 'Trí tuệ cảm xúc (EQ)', 'Daniel Goleman', 190000, 25, 'Tâm lý', 'Tại sao trí tuệ cảm xúc có thể quan trọng hơn chỉ số thông minh IQ trong thành công cuộc sống.'),
    (139, 'Search Inside Yourself', 'Chade-Meng Tan', 150000, 35, 'Kỹ năng sống', 'Giáo trình thiền định và phát triển trí tuệ cảm xúc nổi tiếng của Google.'),
    (140, 'Hiểu về trái tim', 'Minh Niệm', 145000, 70, 'Tâm linh', 'Những bài viết sâu sắc giúp chữa lành vết thương tâm hồn và tìm lại hạnh phúc chân thật.'),

    # --- Văn học Việt Nam & Tản văn ---
    (141, 'Cánh đồng bất tận', 'Nguyễn Ngọc Tư', 85000, 60, 'Văn học VN', 'Tuyển tập truyện ngắn khắc họa thân phận con người miền Tây sông nước đầy ám ảnh và day dứt.'),
    (142, 'Đảo của người ngụ cư', 'Đỗ Phước Tiến', 90000, 30, 'Văn học VN', 'Câu chuyện về sự cô đơn và những khát khao bị kìm nén trong một không gian tù túng.'),
    (143, 'Nỗi buồn chiến tranh', 'Bảo Ninh', 120000, 40, 'Văn học VN', 'Hồi ức đau thương và ám ảnh về chiến tranh qua cái nhìn của một người lính Bắc Việt.'),
    (144, 'Tuổi thơ dữ dội', 'Phùng Quán', 160000, 50, 'Văn học VN', 'Câu chuyện hào hùng và xúc động về đội thiếu niên trinh sát vệ quốc quân Huế.'),
    (145, 'Quân khu Nam Đồng', 'Bình Ca', 140000, 45, 'Văn học VN', 'Hồi ức về tuổi thơ nghịch ngợm nhưng đầy tình nghĩa của con em cán bộ quân đội thời bao cấp.'),
    (146, 'Búp sen xanh', 'Sơn Tùng', 95000, 70, 'Văn học VN', 'Tiểu thuyết lịch sử tái hiện thời niên thiếu và tuổi trẻ của chủ tịch Hồ Chí Minh.'),
    (147, 'Lá nằm trong lá', 'Nguyễn Nhật Ánh', 105000, 65, 'Văn học VN', 'Câu chuyện nhẹ nhàng về tình bạn, tình yêu tuổi học trò và những rung động đầu đời.'),
    (148, 'Có hai con mèo ngồi bên cửa sổ', 'Nguyễn Nhật Ánh', 90000, 80, 'Thiếu nhi', 'Tình bạn kỳ lạ giữa một con mèo và một con chuột, mang thông điệp về tình yêu thương.'),
    (149, 'Ngồi khóc trên cây', 'Nguyễn Nhật Ánh', 110000, 60, 'Tiểu thuyết', 'Câu chuyện tình yêu trong trẻo nhưng cũng đầy trắc trở giữa núi rừng phương Nam.'),
    (150, 'Thương nhớ mười hai', 'Vũ Bằng', 80000, 40, 'Văn học VN', 'Tản văn tuyệt đẹp về nỗi nhớ Hà Nội và phong vị mười hai tháng trong năm của người xa quê.'),

    # --- Văn học Kinh điển Thế giới (Bổ sung) ---
    (151, '1984', 'George Orwell', 110000, 50, 'Tiểu thuyết', 'Tác phẩm phản địa đàng kinh điển về sự giám sát toàn diện và sự mất tự do của con người.'),
    (152, 'Trại súc vật (Animal Farm)', 'George Orwell', 80000, 60, 'Tiểu thuyết', 'Truyện ngụ ngôn chính trị sâu cay về quyền lực và sự tha hóa thông qua một nông trại súc vật.'),
    (153, 'Bắt trẻ đồng xanh', 'J.D. Salinger', 95000, 55, 'Tiểu thuyết', 'Câu chuyện về sự nổi loạn, cô đơn và hoang mang của tuổi mới lớn qua lời kể của Holden Caulfield.'),
    (154, 'Đồi gió hú', 'Emily Brontë', 120000, 35, 'Tiểu thuyết', 'Câu chuyện tình yêu cuồng nhiệt, ám ảnh và đầy hận thù giữa Heathcliff và Catherine.'),
    (155, 'Jane Eyre', 'Charlotte Brontë', 130000, 35, 'Tiểu thuyết', 'Hành trình vượt qua định kiến và tìm kiếm hạnh phúc của một cô gái nghèo nhưng giàu nghị lực.'),
    (156, 'Chuông nguyện hồn ai', 'Ernest Hemingway', 180000, 20, 'Tiểu thuyết', 'Bức tranh bi tráng về cuộc nội chiến Tây Ban Nha và giá trị của sự hy sinh.'),
    (157, 'Don Quixote', 'Miguel de Cervantes', 250000, 15, 'Tiểu thuyết', 'Câu chuyện hài hước nhưng đầy ý nghĩa về hiệp sĩ quý tộc tài ba xứ Mancha.'),
    (158, 'Ba chàng lính ngự lâm', 'Alexandre Dumas', 190000, 25, 'Tiểu thuyết', 'Cuộc phiêu lưu hào hiệp của d\'Artagnan và ba người bạn lính ngự lâm Athos, Porthos, Aramis.'),
    (159, 'Bá tước Monte Cristo', 'Alexandre Dumas', 300000, 15, 'Tiểu thuyết', 'Hành trình báo thù vĩ đại và ly kỳ nhất trong lịch sử văn học của Edmond Dantès.'),
    (160, 'Anna Karenina', 'Leo Tolstoy', 220000, 20, 'Tiểu thuyết', 'Bi kịch tình yêu và bức tranh xã hội Nga thế kỷ 19 qua cuộc đời của Anna Karenina.'),

    # --- Khoa học, Lịch sử & Tri thức ---
    (161, 'Factfulness (Sự thật về thế giới)', 'Hans Rosling', 170000, 30, 'Khoa học', 'Mười bản năng khiến chúng ta hiểu sai về thế giới và tại sao mọi thứ đang tốt đẹp hơn bạn nghĩ.'),
    (162, 'Lược sử vạn vật', 'Bill Bryson', 250000, 15, 'Khoa học', 'Hành trình khám phá khoa học từ Big Bang đến văn minh nhân loại với giọng văn hài hước.'),
    (163, 'Những người khổng lồ (Titan)', 'Ron Chernow', 350000, 10, 'Tiểu sử', 'Tiểu sử chi tiết về John D. Rockefeller, người giàu nhất lịch sử hiện đại.'),
    (164, 'Leonardo da Vinci', 'Walter Isaacson', 320000, 15, 'Tiểu sử', 'Cuộc đời và sự sáng tạo vô biên của thiên tài toàn năng nhất lịch sử nhân loại.'),
    (165, 'Einstein: Cuộc đời và vũ trụ', 'Walter Isaacson', 280000, 20, 'Tiểu sử', 'Câu chuyện về nhà vật lý vĩ đại nhất thế kỷ 20 và cách tư duy phá vỡ mọi quy tắc.'),
    (166, 'Mật mã tài năng', 'Daniel Coyle', 140000, 30, 'Kỹ năng sống', 'Khám phá cơ chế sinh học thần kinh đằng sau việc phát triển kỹ năng và tài năng.'),
    (167, 'Phiêu bạt giữa các vì sao', 'Jack London', 110000, 25, 'Tiểu thuyết', 'Câu chuyện kỳ lạ về sức mạnh tinh thần và khả năng du hành qua các kiếp sống.'),
    (168, 'Chó hoang Dingo', 'R. Fraerman', 75000, 40, 'Thiếu nhi', 'Câu chuyện đẹp và buồn về tình đầu tuổi học trò trong trẻo.'),
    (169, 'Ruồi trâu', 'Ethel Lilian Voynich', 100000, 45, 'Tiểu thuyết', 'Bản anh hùng ca về lý tưởng cách mạng và tình yêu đầy bi kịch của Arthur.'),
    (170, 'Thép đã tôi thế đấy', 'Nikolai Ostrovsky', 130000, 35, 'Tiểu thuyết', 'Cuộc đời đầy nhiệt huyết và cống hiến của Pavel Korchagin cho lý tưởng cao đẹp.'),

    # --- Sách nuôi dạy con & Gia đình ---
    (171, 'Vô cùng tàn nhẫn vô cùng yêu thương', 'Sara Imas', 120000, 50, 'Kỹ năng sống', 'Phương pháp giáo dục con cái tự lập và thành công của người Do Thái.'),
    (172, 'Chờ đến mẫu giáo thì đã muộn', 'Ibuka Masaru', 95000, 60, 'Kỹ năng sống', 'Tầm quan trọng của giáo dục sớm trong giai đoạn vàng từ 0 đến 3 tuổi.'),
    (173, 'Nuôi con không phải là cuộc chiến', 'Nhiều tác giả', 150000, 50, 'Kỹ năng sống', 'Cẩm nang giúp cha mẹ hiểu và chăm sóc trẻ sơ sinh một cách khoa học và nhẹ nhàng.'),
    (174, 'Con cái chúng ta giỏi thật', 'Azuma Kanako', 80000, 40, 'Kỹ năng sống', 'Cách rèn luyện thói quen sinh hoạt và ý thức trách nhiệm cho trẻ em Nhật Bản.'),
    (175, 'Để con được ốm', 'Uyên Bùi', 110000, 55, 'Sức khỏe', 'Kiến thức y khoa thường thức giúp cha mẹ bớt lo lắng khi con ốm vặt.'),

    # --- Truyện tranh & Manga (Bổ sung) ---
    (176, 'One Punch Man', 'ONE & Murata', 25000, 150, 'Truyện tranh', 'Siêu anh hùng mạnh nhất vũ trụ nhưng lại bị hói đầu và chán nản vì không có đối thủ.'),
    (177, 'Death Note', 'Tsugumi Ohba', 35000, 80, 'Truyện tranh', 'Cuộc đấu trí căng thẳng giữa kẻ nắm giữ cuốn sổ tử thần và thám tử lập dị L.'),
    (178, 'Fullmetal Alchemist', 'Hiromu Arakawa', 40000, 90, 'Truyện tranh', 'Hành trình tìm kiếm Hòn đá Triết gia của hai anh em giả kim thuật sư Edward và Alphonse.'),
    (179, 'Tokyo Revengers', 'Ken Wakui', 45000, 100, 'Truyện tranh', 'Du hành thời gian về quá khứ để cứu người yêu và thay đổi vận mệnh băng đảng học đường.'),
    (180, 'Slam Dunk', 'Takehiko Inoue', 35000, 70, 'Truyện tranh', 'Huyền thoại bóng rổ học đường, câu chuyện về nỗ lực và đam mê của Hanamichi Sakuragi.'),
    (181, 'Haikyuu!! (Vua bóng chuyền)', 'Haruichi Furudate', 30000, 120, 'Truyện tranh', 'Nhiệt huyết tuổi trẻ và tinh thần đồng đội trong môn bóng chuyền.'),
    (182, 'Gintama', 'Hideaki Sorachi', 25000, 60, 'Truyện tranh', 'Câu chuyện hài hước bựa nhầy về samurai thời hiện đại trong bối cảnh người ngoài hành tinh xâm lược.'),
    (183, 'Bleach', 'Tite Kubo', 25000, 90, 'Truyện tranh', 'Ichigo Kurosaki trở thành Tử thần thay thế để bảo vệ con người khỏi những linh hồn xấu xa.'),
    (184, 'Fairy Tail', 'Hiro Mashima', 25000, 110, 'Truyện tranh', 'Những cuộc phiêu lưu phép thuật kỳ thú của hội pháp sư Fairy Tail.'),
    (185, 'My Hero Academia', 'Kohei Horikoshi', 30000, 130, 'Truyện tranh', 'Hành trình trở thành siêu anh hùng số một của cậu bé vô năng Deku.'),

    # --- Du ký & Khám phá ---
    (186, 'Xách ba lô lên và đi', 'Huyền Chip', 110000, 40, 'Du ký', 'Hành trình du lịch bụi qua 25 nước với chi phí rẻ và những trải nghiệm nhớ đời.'),
    (187, 'Tôi là một con lừa', 'Nguyễn Phương Mai', 95000, 35, 'Du ký', 'Những chuyến đi khám phá văn hóa và con người ở những vùng đất xa xôi, ít người biết.'),
    (188, 'Con đường Hồi giáo', 'Nguyễn Phương Mai', 130000, 30, 'Du ký', 'Hành trình dấn thân vào thế giới Hồi giáo đầy bí ẩn và những góc nhìn chân thực.'),
    (189, 'Chân đi không mỏi', 'Đinh Hằng', 100000, 45, 'Du ký', 'Hành trình khám phá thế giới và tìm lại bản thân của một cô gái trẻ đầy nhiệt huyết.'),
    (190, 'Bên rặng Tuyết Sơn', 'Swami Amar Jyoti', 85000, 50, 'Tâm linh', 'Hành trình tâm linh tìm kiếm chân lý và sự giác ngộ trên dãy Himalaya huyền bí.'),

    # --- Sách chuyên khảo khác ---
    (191, 'Dữ liệu lớn (Big Data)', 'Viktor Mayer-Schönberger', 160000, 20, 'Công nghệ', 'Cách dữ liệu lớn đang thay đổi cách chúng ta sống, làm việc và tư duy.'),
    (192, 'Cuộc cách mạng nền tảng', 'Geoffrey G. Parker', 180000, 15, 'Kinh tế', 'Mô hình kinh doanh nền tảng (Platform) đang thống trị thế giới như Uber, Airbnb, Facebook.'),
    (193, 'Marketing 4.0', 'Philip Kotler', 120000, 40, 'Kinh doanh', 'Dịch chuyển từ marketing truyền thống sang kỹ thuật số trong nền kinh tế số.'),
    (194, 'Tư duy thiết kế (Design Thinking)', 'Nhiều tác giả', 150000, 25, 'Kỹ năng sống', 'Phương pháp giải quyết vấn đề sáng tạo lấy con người làm trung tâm.'),
    (195, 'Lược sử loài người (Graphic Novel)', 'Yuval Noah Harari', 250000, 20, 'Truyện tranh', 'Phiên bản truyện tranh sinh động và dễ hiểu của cuốn sách bán chạy Sapiens.'),
    (196, 'Tiếng Anh Ma Thuật', 'Woo Bo Hyun', 110000, 60, 'Ngoại ngữ', 'Phương pháp học tiếng Anh độc đáo và thú vị của tác giả người Hàn Quốc.'),
    (197, 'Vừa lười vừa bận vẫn giỏi tiếng Anh', 'Nguyễn Văn Hiệp', 160000, 50, 'Ngoại ngữ', 'Giải pháp học tiếng Anh giao tiếp hiệu quả cho người đi làm bận rộn.'),
    (198, 'Dinh dưỡng học bị thất truyền', 'Vương Đào', 130000, 40, 'Sức khỏe', 'Đẩy lùi bệnh tật bằng dinh dưỡng và khả năng tự phục hồi của cơ thể.'),
    (199, 'Hệ miễn dịch - Kiệt tác của sự sống', 'Cao Bảo Anh', 180000, 30, 'Sức khỏe', 'Khám phá hệ thống phòng thủ phức tạp và kỳ diệu bảo vệ cơ thể con người.'),
    (200, 'Nghệ thuật tinh tế của việc đếch quan tâm', 'Mark Manson', 110000, 55, 'Kỹ năng sống', 'Cách sống bớt lo âu bằng việc chọn lọc những điều thực sự đáng để quan tâm.'),
    # --- Văn học Kinh điển & Triết học ---
    (201, 'Chiến tranh và hòa bình', 'Leo Tolstoy', 350000, 15, 'Tiểu thuyết', 'Bức tranh vĩ đại về nước Nga thời chiến tranh Napoleon và những suy ngẫm sâu sắc về lịch sử.'),
    (202, 'Anh em nhà Karamazov', 'Fyodor Dostoevsky', 280000, 20, 'Tiểu thuyết', 'Cuộc đấu tranh giữa đức tin và hoài nghi, lý trí và tình cảm trong một gia đình đầy mâu thuẫn.'),
    (203, 'Hóa thân (The Metamorphosis)', 'Franz Kafka', 90000, 35, 'Tiểu thuyết', 'Câu chuyện phi lý về Gregor Samsa thức dậy và thấy mình biến thành một con bọ khổng lồ.'),
    (204, 'Người xa lạ', 'Albert Camus', 100000, 40, 'Triết học', 'Tác phẩm hiện sinh kinh điển về sự thờ ơ của con người trước cái chết và sự vô nghĩa của cuộc đời.'),
    (205, 'Truyện Kiều', 'Nguyễn Du', 120000, 100, 'Văn học VN', 'Kiệt tác thơ Nôm của văn học Việt Nam về cuộc đời truân chuyên của nàng Thúy Kiều.'),
    (206, 'Lục Vân Tiên', 'Nguyễn Đình Chiểu', 65000, 50, 'Văn học VN', 'Truyện thơ đề cao đạo lý làm người, nhân nghĩa và tinh thần trượng nghĩa.'),
    (207, 'Cộng hòa (The Republic)', 'Plato', 220000, 25, 'Triết học', 'Tác phẩm nền tảng của triết học phương Tây bàn về công lý, nhà nước lý tưởng và con người.'),
    (208, 'Bên kia thiện ác', 'Friedrich Nietzsche', 160000, 30, 'Triết học', 'Sự phê phán gay gắt đối với các giá trị đạo đức truyền thống và tôn giáo phương Tây.'),
    (209, 'Đạo Đức Kinh', 'Lão Tử', 110000, 60, 'Triết học', 'Tinh hoa triết học Đạo gia về quy luật tự nhiên, sự vô vi và cách sống hòa hợp với trời đất.'),
    (210, 'Binh pháp Tôn Tử', 'Tôn Tử', 95000, 80, 'Kinh doanh', 'Những nguyên tắc chiến lược quân sự cổ đại nhưng vẫn nguyên giá trị trong quản trị và kinh doanh hiện đại.'),

    # --- Tiểu thuyết Lãng mạn & Young Adult (YA) ---
    (211, 'Khi lỗi thuộc về những vì sao', 'John Green', 105000, 50, 'Tiểu thuyết', 'Câu chuyện tình yêu đẫm nước mắt nhưng đầy lạc quan của hai bạn trẻ mắc bệnh ung thư.'),
    (212, 'Trước ngày em đến (Me Before You)', 'Jojo Moyes', 130000, 45, 'Tiểu thuyết', 'Chuyện tình éo le giữa cô gái chăm sóc lạc quan và chàng trai liệt tứ chi muốn kết thúc cuộc đời.'),
    (213, 'Chạng vạng (Twilight)', 'Stephenie Meyer', 140000, 35, 'Tiểu thuyết', 'Mối tình lãng mạn và nguy hiểm giữa cô nữ sinh Bella Swan và chàng ma cà rồng Edward Cullen.'),
    (214, 'Kiêu hãnh và định kiến', 'Jane Austen', 120000, 55, 'Tiểu thuyết', 'Cuộc đối đầu thú vị giữa Elizabeth Bennet thông minh và quý ngài Darcy kiêu ngạo.'),
    (215, 'Cuốn theo chiều gió', 'Margaret Mitchell', 260000, 20, 'Tiểu thuyết', 'Sử thi về tình yêu và nghị lực sống của Scarlett O\'Hara giữa bối cảnh nội chiến Mỹ hoang tàn.'),
    (216, 'Gọi em bằng tên anh', 'André Aciman', 115000, 30, 'Tiểu thuyết', 'Câu chuyện tình mùa hè nồng nàn và đầy day dứt tại Ý giữa Elio và chàng học giả Oliver.'),
    (217, 'Con nhà siêu giàu châu Á', 'Kevin Kwan', 170000, 40, 'Tiểu thuyết', 'Cái nhìn hài hước và châm biếm về giới thượng lưu giàu có bậc nhất Singapore.'),
    (218, 'Rừng Na Uy', 'Haruki Murakami', 150000, 45, 'Tiểu thuyết', 'Bản tình ca u sầu về sự mất mát, cô đơn và dục vọng của tuổi trẻ Nhật Bản.'),
    (219, '5 Centimet trên giây', 'Shinkai Makoto', 60000, 70, 'Tiểu thuyết', 'Ba câu chuyện nhỏ về khoảng cách, thời gian và những mối tình đầu không thể lãng quên.'),
    (220, 'Em sẽ đến cùng cơn mưa', 'Ichikawa Takuji', 95000, 50, 'Tiểu thuyết', 'Câu chuyện giả tưởng cảm động về người vợ đã mất quay trở lại vào mùa mưa để gặp chồng con.'),

    # --- Sci-Fi & Giả tưởng Hiện đại ---
    (221, 'Người về từ sao Hỏa (The Martian)', 'Andy Weir', 145000, 35, 'Tiểu thuyết', 'Hành trình sinh tồn phi thường của một phi hành gia bị bỏ lại một mình trên sao Hỏa.'),
    (222, 'Trò chơi ảo giác (Ready Player One)', 'Ernest Cline', 160000, 30, 'Tiểu thuyết', 'Cuộc săn tìm kho báu trong thế giới ảo OASIS nơi văn hóa Pop thập niên 80 lên ngôi.'),
    (223, 'Trò chơi của Ender (Ender\'s Game)', 'Orson Scott Card', 150000, 25, 'Tiểu thuyết', 'Cậu bé thiên tài quân sự được huấn luyện để chỉ huy cuộc chiến chống lại người ngoài hành tinh.'),
    (224, 'Biên niên sử Narnia: Sư tử, Phù thủy và Tủ áo', 'C.S. Lewis', 90000, 60, 'Tiểu thuyết', 'Bốn anh em bước qua cánh cửa tủ áo để đến vùng đất Narnia huyền bí đang bị đóng băng vĩnh cửu.'),
    (225, 'Trò chơi vương quyền (A Game of Thrones)', 'George R.R. Martin', 280000, 15, 'Tiểu thuyết', 'Cuộc chiến tranh giành ngai sắt đẫm máu giữa các gia tộc tại lục địa Westeros.'),
    (226, 'Xứ Cát (Dune)', 'Frank Herbert', 220000, 20, 'Tiểu thuyết', 'Sử thi viễn tưởng về chính trị, tôn giáo và sinh thái học trên hành tinh sa mạc Arrakis.'),
    (227, 'Người máy có mơ về cừu điện không?', 'Philip K. Dick', 130000, 30, 'Tiểu thuyết', 'Nguyên tác của phim Blade Runner, đặt câu hỏi về ranh giới giữa con người và trí tuệ nhân tạo.'),
    (228, 'Chúa tể của những loài ruồi', 'William Golding', 110000, 40, 'Tiểu thuyết', 'Sự sụp đổ của văn minh và trỗi dậy của bản năng hoang dã khi một nhóm trẻ em bị kẹt trên đảo hoang.'),
    (229, 'Vụ trụ trong vỏ hạt dẻ', 'Stephen Hawking', 180000, 25, 'Khoa học', 'Phần tiếp theo của Lược sử thời gian, giải thích các khái niệm vũ trụ phức tạp bằng hình ảnh minh họa.'),
    (230, 'Lược sử vạn vật', 'Bill Bryson', 250000, 15, 'Khoa học', 'Hành trình khám phá khoa học từ Big Bang đến văn minh nhân loại với giọng văn hài hước.'),

    # --- Tài chính & Đầu tư ---
    (231, 'Nhà đầu tư thông minh', 'Benjamin Graham', 280000, 20, 'Kinh tế', 'Kinh thánh về đầu tư giá trị, cuốn sách gối đầu giường của Warren Buffett.'),
    (232, 'Phân tích chứng khoán', 'Benjamin Graham', 350000, 10, 'Kinh tế', 'Giáo trình chuyên sâu về phân tích báo cáo tài chính và định giá doanh nghiệp.'),
    (233, 'Trên đỉnh phố Wall', 'Peter Lynch', 190000, 25, 'Kinh tế', 'Phương pháp đầu tư vào những gì bạn hiểu rõ để đánh bại thị trường.'),
    (234, 'Tâm lý học về tiền', 'Morgan Housel', 165000, 45, 'Kinh tế', 'Những bài học vượt thời gian về sự giàu có, tham lam và hạnh phúc tài chính.'),
    (235, 'Những nguyên tắc (Principles)', 'Ray Dalio', 320000, 15, 'Kinh doanh', 'Hệ thống nguyên tắc sống và làm việc đã giúp Ray Dalio xây dựng quỹ đầu tư lớn nhất thế giới.'),
    (236, 'Gã nghiện giày (Shoe Dog)', 'Phil Knight', 185000, 30, 'Kinh doanh', 'Hồi ký chân thực và đầy cảm hứng của nhà sáng lập Nike về hành trình khởi nghiệp gian nan.'),
    (237, 'Khác biệt để bứt phá (Rework)', 'Jason Fried', 120000, 40, 'Kinh doanh', 'Cách tiếp cận kinh doanh hiện đại: Ít họp hành hơn, không cần vốn lớn và bỏ qua đối thủ cạnh tranh.'),
    (238, 'Tuần làm việc 4 giờ', 'Tim Ferriss', 160000, 35, 'Kỹ năng sống', 'Làm thế nào để thoát khỏi kiếp làm thuê 9-5, sống ở bất cứ đâu và gia nhập tầng lớp "Nhà giàu mới".'),
    (239, 'Mô hình kinh doanh (Business Model Generation)', 'Alexander Osterwalder', 250000, 20, 'Kinh doanh', 'Cẩm nang xây dựng mô hình kinh doanh trực quan dành cho những người kiến tạo và thay đổi cuộc chơi.'),
    (240, 'Bí mật Dotcom', 'Russell Brunson', 180000, 25, 'Kinh doanh', 'Các chiến lược marketing online để xây dựng phễu bán hàng và tăng trưởng doanh nghiệp đột phá.'),

    # --- Manga & Light Novel (Bổ sung mạnh) ---
    (241, 'Thám tử lừng danh Conan (Tập 101)', 'Gosho Aoyama', 25000, 200, 'Truyện tranh', 'Vụ án mới nhất liên quan đến Tổ chức Áo đen và những màn đấu trí nghẹt thở.'),
    (242, 'Inuyasha (Khuyển Dạ Xoa)', 'Rumiko Takahashi', 30000, 80, 'Truyện tranh', 'Cuộc phiêu lưu xuyên không về thời Chiến Quốc của Kagome và bán yêu Inuyasha.'),
    (243, 'Ranma 1/2', 'Rumiko Takahashi', 30000, 70, 'Truyện tranh', 'Câu chuyện hài hước về chàng võ sĩ biến thành con gái khi dội nước lạnh.'),
    (244, 'Thủy thủ mặt trăng (Sailor Moon)', 'Naoko Takeuchi', 35000, 100, 'Truyện tranh', 'Những nữ chiến binh thủy thủ xinh đẹp bảo vệ trái đất khỏi thế lực hắc ám.'),
    (245, 'Vua trò chơi (Yu-Gi-Oh!)', 'Kazuki Takahashi', 25000, 90, 'Truyện tranh', 'Yugi và những trận đấu bài ma thuật đỉnh cao triệu hồi quái thú.'),
    (246, 'Thủ lĩnh thẻ bài (Cardcaptor Sakura)', 'CLAMP', 40000, 85, 'Truyện tranh', 'Cô bé Sakura thu phục các thẻ bài phép thuật Clow bị thất lạc.'),
    (247, 'Berserk (Kiếm sĩ đen)', 'Kentaro Miura', 50000, 60, 'Truyện tranh', 'Hành trình báo thù đẫm máu và bi tráng của kiếm sĩ Guts trong thế giới đen tối.'),
    (248, 'Vagabond (Lãng khách)', 'Takehiko Inoue', 45000, 50, 'Truyện tranh', 'Cuộc đời của kiếm thánh Miyamoto Musashi qua nét vẽ nghệ thuật đỉnh cao.'),
    (249, 'Monster', 'Naoki Urasawa', 40000, 40, 'Truyện tranh', 'Bác sĩ Tenma truy đuổi một con quái vật tâm thần mà chính anh đã cứu sống năm xưa.'),
    (250, '20th Century Boys', 'Naoki Urasawa', 40000, 45, 'Truyện tranh', 'Nhóm bạn thời thơ ấu phải ngăn chặn một giáo phái kỳ lạ muốn hủy diệt thế giới theo kịch bản họ từng viết.'),
    (251, 'Sword Art Online (Light Novel)', 'Reki Kawahara', 90000, 120, 'Tiểu thuyết', 'Mắc kẹt trong trò chơi thực tế ảo tử thần, nơi cái chết trong game là cái chết ngoài đời thực.'),
    (252, 'Overlord (Light Novel)', 'Kugane Maruyama', 100000, 80, 'Tiểu thuyết', 'Một game thủ bị kẹt trong thân xác nhân vật Ma Vương bá đạo tại thế giới khác.'),
    (253, 'Chuyển sinh thành Slime (Light Novel)', 'Fuse', 95000, 90, 'Tiểu thuyết', 'Anh chàng nhân viên văn phòng chết đi và tái sinh thành một con Slime yếu nhớt nhưng có kỹ năng bá đạo.'),
    (254, 'No Game No Life', 'Yuu Kamiya', 95000, 70, 'Tiểu thuyết', 'Hai anh em game thủ thiên tài được triệu hồi đến thế giới nơi mọi thứ quyết định bằng trò chơi.'),
    (255, 'Dáng hình thanh âm', 'Yoshitoki Oima', 35000, 60, 'Truyện tranh', 'Câu chuyện cảm động về sự bắt nạt, hối hận và sự tha thứ giữa một chàng trai và cô gái khiếm thính.'),

    # --- Lịch sử & Văn hóa Việt Nam ---
    (256, 'Việt Nam Sử Lược', 'Trần Trọng Kim', 180000, 50, 'Lịch sử', 'Bộ thông sử Việt Nam đầu tiên viết bằng chữ Quốc ngữ, ngắn gọn và dễ hiểu.'),
    (257, 'Đại Việt Sử Ký Toàn Thư', 'Ngô Sĩ Liên', 450000, 10, 'Lịch sử', 'Bộ chính sử đồ sộ ghi chép lịch sử Việt Nam từ thời Hồng Bàng đến thời Hậu Lê.'),
    (258, 'Hà Nội băm sáu phố phường', 'Thạch Lam', 75000, 60, 'Văn học VN', 'Những trang văn tinh tế miêu tả vẻ đẹp và ẩm thực của Hà Nội xưa.'),
    (259, 'Thương nhớ mười hai', 'Vũ Bằng', 85000, 55, 'Văn học VN', 'Nỗi nhớ da diết về phong tục, món ăn và cảnh sắc Bắc Bộ của một người con xa xứ.'),
    (260, 'Miếng ngon Hà Nội', 'Vũ Bằng', 80000, 50, 'Văn học VN', 'Tác phẩm sành ăn ca ngợi những món đặc sản tinh túy của đất kinh kỳ.'),
    (261, 'Đất lề quê thói', 'Nhất Thanh', 150000, 30, 'Văn hóa', 'Bách khoa toàn thư về phong tục tập quán, lễ nghi và nếp sống cổ truyền của người Việt.'),
    (262, 'Lĩnh Nam Chích Quái', 'Trần Thế Pháp', 110000, 40, 'Văn học VN', 'Tập hợp những truyền thuyết và truyện kỳ lạ ở nước Nam như Thánh Gióng, Chử Đồng Tử.'),
    (263, 'Truyền kỳ mạn lục', 'Nguyễn Dữ', 95000, 45, 'Văn học VN', 'Được mệnh danh là "Thiên cổ kỳ bút", ghi chép những chuyện kỳ quái lưu truyền trong dân gian.'),
    (264, 'Hồn Trương Ba, da hàng thịt', 'Lưu Quang Vũ', 70000, 40, 'Văn học VN', 'Vở kịch kinh điển đầy triết lý nhân sinh về sự mâu thuẫn giữa thể xác và tâm hồn.'),
    (265, 'Nhật ký trong tù', 'Hồ Chí Minh', 80000, 100, 'Văn học VN', 'Tập thơ chữ Hán ghi lại những suy ngẫm và khí phách của Bác trong thời gian bị giam cầm.'),

    # --- Tâm lý tội phạm & Kinh dị ---
    (266, 'Sự im lặng của bầy cừu', 'Thomas Harris', 145000, 50, 'Trinh thám', 'Bác sĩ Hannibal Lecter giúp FBI truy tìm kẻ giết người hàng loạt qua những gợi ý bệnh hoạn.'),
    (267, 'Rồng Đỏ', 'Thomas Harris', 140000, 40, 'Trinh thám', 'Phần tiền truyện về Hannibal Lecter và cuộc săn đuổi tên sát nhân "Tiên Răng".'),
    (268, 'Hannibal', 'Thomas Harris', 150000, 35, 'Trinh thám', 'Sự trở lại của bác sĩ ăn thịt người và cuộc rượt đuổi đẫm máu tại Florence.'),
    (269, 'Kỳ án ánh trăng', 'Quỷ Cổ Nữ', 120000, 45, 'Kinh dị', 'Tiểu thuyết kinh dị Trung Quốc về những cái chết bí ẩn tại ký túc xá đại học.'),
    (270, 'Tấm vải đỏ', 'Hồng Nương Tử', 115000, 40, 'Kinh dị', 'Câu chuyện ma quái đầy ám ảnh về lời nguyền của một tấm vải đỏ nhuốm máu.'),
    (271, 'Đau thương (Misery)', 'Stephen King', 160000, 30, 'Kinh dị', 'Một nhà văn bị fan cuồng bắt cóc và ép viết lại kết thúc tiểu thuyết theo ý bà ta.'),
    (272, 'The Shining (Ngôi nhà ma)', 'Stephen King', 170000, 25, 'Kinh dị', 'Khách sạn Overlook bị ma ám khiến người cha dần phát điên và truy sát vợ con.'),
    (273, 'Gã hề ma quái (It)', 'Stephen King', 250000, 15, 'Kinh dị', 'Nhóm trẻ em đối mặt với thực thể tà ác trong hình dạng chú hề Pennywise cứ 27 năm lại xuất hiện.'),
    (274, 'Cô gái mất tích (Gone Girl)', 'Gillian Flynn', 155000, 40, 'Trinh thám', 'Vụ mất tích bí ẩn của người vợ vào kỷ niệm ngày cưới và những bí mật hôn nhân đen tối.'),
    (275, 'Cô gái trên tàu', 'Paula Hawkins', 135000, 45, 'Trinh thám', 'Một người phụ nữ nghiện rượu vô tình chứng kiến một tội ác qua cửa sổ tàu hỏa.'),

    # --- Sách Kiến thức Tổng hợp & Bách khoa ---
    (276, 'Vạn vật vận hành như thế nào?', 'David Macaulay', 290000, 20, 'Khoa học', 'Giải thích nguyên lý hoạt động của mọi thứ từ khóa cửa đến tàu ngầm bằng tranh vẽ vui nhộn.'),
    (277, 'Bách khoa thư Larousse', 'Nhiều tác giả', 450000, 10, 'Giáo dục', 'Kho tàng tri thức khổng lồ cho trẻ em về mọi lĩnh vực trong cuộc sống.'),
    (278, 'Atlas thế giới', 'Nhiều tác giả', 320000, 15, 'Giáo dục', 'Bản đồ chi tiết và thông tin địa lý, kinh tế, văn hóa của các quốc gia trên thế giới.'),
    (279, 'Sổ tay phi hành gia', 'Chris Hadfield', 140000, 30, 'Khoa học', 'Những bài học về cách sống và làm việc trong vũ trụ từ cựu chỉ huy trạm ISS.'),
    (280, 'Giải mã gen (The Gene)', 'Siddhartha Mukherjee', 280000, 15, 'Khoa học', 'Lịch sử khám phá gen di truyền và tương lai của công nghệ chỉnh sửa gen người.'),

    # --- Tản văn & Sách chữa lành (Healing) ---
    (281, 'Mùa trôi trên mái nhà', 'Nguyễn Ngọc Tư', 85000, 50, 'Văn học VN', 'Những tạp văn nhẹ nhàng nhưng thấm đẫm tình người miền Tây.'),
    (282, 'Cà phê cùng Tony', 'Tony Buổi Sáng', 90000, 100, 'Kỹ năng sống', 'Những bài viết hài hước, châm biếm sâu cay khuyên giới trẻ sống hào sảng và văn minh.'),
    (283, 'Trên đường băng', 'Tony Buổi Sáng', 95000, 100, 'Kỹ năng sống', 'Tiếp nối Cà phê cùng Tony, cổ vũ tinh thần khởi nghiệp và bay cao bay xa của người trẻ.'),
    (284, 'Yêu những điều không hoàn hảo', 'Haemin', 125000, 60, 'Tâm linh', 'Cách chấp nhận bản thân và yêu thương những khuyết điểm của chính mình và người khác.'),
    (285, 'Bước chậm lại giữa thế gian vội vã', 'Haemin', 120000, 70, 'Tâm linh', 'Lời khuyên của đại đức Haemin giúp tìm lại sự cân bằng và bình an trong cuộc sống hiện đại.'),
    (286, 'Lagom - Biết đủ là tự do', 'Niki Brantmark', 110000, 40, 'Kỹ năng sống', 'Triết lý sống vừa đủ, cân bằng và hạnh phúc của người Thụy Điển.'),
    (287, 'Sygge - Hạnh phúc từ những điều nhỏ bé', 'Meik Wiking', 115000, 40, 'Kỹ năng sống', 'Bí mật về lối sống ấm cúng và hạnh phúc của người Đan Mạch.'),
    (288, 'Ikigai - Đi tìm lý do thức dậy mỗi sáng', 'Héctor García', 105000, 50, 'Kỹ năng sống', 'Bí quyết sống thọ và hạnh phúc của người Nhật vùng Okinawa.'),
    (289, 'Tối giản - Sở hữu ít đi, hạnh phúc nhiều hơn', 'Joshua Becker', 130000, 35, 'Kỹ năng sống', 'Hướng dẫn thực hành lối sống tối giản để giải phóng không gian và tâm trí.'),
    (290, 'Làm như chơi', 'Minh Niệm', 140000, 45, 'Tâm linh', 'Nghệ thuật làm việc và sống thảnh thơi, không áp lực mà vẫn hiệu quả.'),

    # --- Sách Ngoại văn & Best-seller khác ---
    (291, 'Bố già (Tiếng Anh: The Godfather)', 'Mario Puzo', 200000, 20, 'Ngoại văn', 'Bản gốc tiếng Anh của kiệt tác Bố già dành cho người học tiếng Anh.'),
    (292, 'Harry Potter and the Sorcerer\'s Stone', 'J.K. Rowling', 250000, 30, 'Ngoại văn', 'Tập 1 Harry Potter bản tiếng Anh bìa cứng tuyệt đẹp.'),
    (293, 'Ngàn mặt trời rực rỡ', 'Khaled Hosseini', 160000, 30, 'Tiểu thuyết', 'Câu chuyện cảm động về tình bạn giữa hai người phụ nữ Afghanistan giữa bom đạn chiến tranh.'),
    (294, 'Người đua diều', 'Khaled Hosseini', 155000, 35, 'Tiểu thuyết', 'Hành trình chuộc tội của Amir và tình bạn đầy ám ảnh với Hassan.'),
    (295, 'Kẻ trộm sách', 'Markus Zusak', 170000, 25, 'Tiểu thuyết', 'Câu chuyện về cô bé Liesel ăn trộm sách để tìm niềm vui giữa nước Đức thời Đức Quốc xã.'),
    (296, 'Cuộc đời của Pi', 'Yann Martel', 140000, 40, 'Tiểu thuyết', 'Hành trình lênh đênh trên biển của chàng trai Pi cùng một con hổ Bengal.'),
    (297, 'Ông trùm tài chính (Titan)', 'Ron Chernow', 380000, 10, 'Tiểu sử', 'Câu chuyện về gia tộc Morgan và sự hình thành nền tài chính Mỹ.'),
    (298, 'Máu bẩn (Bad Blood)', 'John Carreyrou', 210000, 20, 'Kinh doanh', 'Vụ lừa đảo thế kỷ của Elizabeth Holmes và công ty Theranos.'),
    (299, 'Tỷ phú bán giày', 'Tony Hsieh', 130000, 40, 'Kinh doanh', 'Văn hóa doanh nghiệp độc đáo của Zappos và hành trình mang lại hạnh phúc.'),
    (300, 'Không bao giờ là thất bại, tất cả là thử thách', 'Chung Ju Yung', 120000, 50, 'Tiểu sử', 'Hồi ký đầy nghị lực của cố chủ tịch tập đoàn Hyundai.')
]

def seed_more_real_books():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    print(f"🔌 Kết nối database: {config.DB_PATH}")
    print(f"🚀 Đang thêm 100 cuốn sách mới (ID 101-200)...")

    count = 0
    skipped = 0
    
    for row in more_books_data:
        # Bỏ qua ID (phần tử đầu tiên) để SQLite tự quản lý hoặc dùng nếu muốn
        _, title, author, price, stock, category, description = row

        try:
            # Check trùng tên
            cursor.execute("SELECT book_id FROM Books WHERE title = ?", (title,))
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute("""
                INSERT INTO Books (title, author, price, stock, category, content)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, author, price, stock, category, description))
            count += 1
        except Exception as e:
            print(f"❌ Lỗi thêm sách '{title}': {e}")

    conn.commit()
    conn.close()
    
    print("------------------------------------------------")
    print(f"✅ Đã thêm thành công: {count} cuốn.")
    print(f"🚫 Bỏ qua (đã có): {skipped} cuốn.")
    print("------------------------------------------------")
    print("⚡ QUAN TRỌNG: Hãy chạy lại file 'build_embeddings.py'")
    print("   để hệ thống cập nhật nội dung tìm kiếm mới!")

if __name__ == "__main__":
    seed_more_real_books()
