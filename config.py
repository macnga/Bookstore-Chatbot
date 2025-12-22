# Lưu trữ thông tin chung và nội dung prompt
import os

GOOGLE_API_KEY = os.getenv(GOOGLE_API_KEY)
DB_PATH = '.\\bookstore.db'

STORE_INFO = """
    "name": "Tiệm sách của Nga nè",
    "address": "Số 201, Đặng Tiến Đông, Đống Đa, Hà Nội",
    "phone": "0888888888",
    "opening_hours": "8:00 tối - 6:00 sáng tất cả các ngày trong tuần (trừ ngày lễ)",
    "return_policy": "Đổi trả trong 3 ngày (kể từ khi nhận hàng) nếu lỗi in ấn. Không áp dụng đổi trả cho các trường hợp khác.",
    "ship_policy": "Phí ship được tính khi lên đơn.",
    "Pay_method": "Thanh toán cho nhân viên giao hàng khi nhận hàng."
"""

OTHER_RESPONSE = "Xin lỗi, mình chỉ hỗ trợ các vấn đề về sách và đơn hàng."

DB_SCHEMA = """
Table Books: book_id, title, author, price, stock, category.
Table Oders: order_id, customer_name, phone, address, total_amount, status, create_at.
Table Details: detail_id, order_id, book_id, quantity, price_at_purchase.
"""

ORDER_STATUS_MAP = {
    "confirming": "⏳ Đang chờ bạn xác nhận",
    "pending": "📦 Đang chờ giao hàng (Shop đang đóng gói)",
    "shipping": "🚚 Đang giao hàng",
    "received": "✅ Đã giao thành công",
    "cancel": "Đơn đã bị hủy."
}
