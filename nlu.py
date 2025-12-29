# Thực hiện phân loại intent và trích xuất các thông tin cần thiết
#Version 29.12.2025 - Add entity confirm để xác định ý định khi đưa đơn confirming

import json
import os
from google import genai
from google.genai import types
from config import GOOGLE_API_KEY, STORE_INFO

client = genai.Client(
    api_key=GOOGLE_API_KEY
    )

def analyze_input(user_input, chat_history):
    recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history

    system_prompt = """
    Bạn là bộ não NLU. Nhiệm vụ: Phân tích Input hiện tại + Lịch sử hội thoại để trả về JSON cấu trúc.

    1. INTENT (Chọn 1):
    - "search_book": Tìm sách, hỏi giá, so sánh sách, hỏi tồn kho.
    - "recommend_book": Nhờ tư vấn, chưa có tên sách cụ thể.
    - "place_order": Hành động mua, chốt đơn, cung cấp thông tin cá nhân để đặt đơn.
    - "order_management": Tra cứu đơn hàng, hủy đơn.
    - "general_support": Chào hỏi, hỗ trợ chung.
    - "other": Ngoài phạm vi. 

    2. ENTITIES (Trích xuất thông tin):
    - book_keywords (list[object]): Danh sách sách muốn mua. Cấu trúc mỗi item:
        * book (string): Tên sách
        * quantity (int): Số lượng (mặc định là 1).
    - author_keywords (list[str]): Tên tác giả.
    - category_keywords (list[str]): Thể loại. VD: "Trinh thám", "Kinh tế".
    - filters (object):
        * min_price (number/null): Giá thấp nhất. VD: "Trên 50k" -> 50000.
        * max_price (number/null): Giá cao nhất. VD: "Dưới 100k" -> 100000.
        * sort_by (string/null): "best_selling" | "newest" | "price_asc" | "price_desc"
    - customer_info (object):
        * name (string): Tên khách hàng
        * phone (string): Số điện thoại
        * address (string): Địa chỉ nhận hàng
    - confirm (string/null): "yes" | "no" | "refine" (Dùng khi khách xác nhận, chỉnh sửa hoặc từ chối đơn hàng)

    VÍ DỤ MẪU:
    User: "shop có nhà giả kim không?"
    Output: {
    "intent": "search_book",
    "entities": {"book_keywords": [{"book": "nhà giả kim", "quantity": 1}]   }
    }

    User: "quyển đắc nhân tâm giá bao nhiêu"
    Output: {
      "intent": "search_book",
      "entities": { "book_keywords": [{"book": "đắc nhân tâm", "quantity": 1}] }
    }

    User: "lấy cho mình cuốn đó nha" (Context trước đó đang nói về Harry Potter)
    Output: {
      "intent": "place_order",
      "entities": { "book_keywords": [{"book": "Harry Potter", "quantity": 1}] }
    }

    LƯU Ý QUAN TRỌNG:
    - XỬ LÝ LỊCH SỬ: Nếu user dùng đại từ như "quyển đó", "nó", "quyển vừa rồi", hãy tìm tên sách tương ứng trong lịch sử hội thoại để điền vào book_keywords.
    - SÁCH HOT: Nếu user nói "Sách hot nhất", book_keywords là [], sort_by là "best_selling".
    - GIÁ: Tự động đổi "k" thành "000" (VD: 50k -> 50000).
    - OUTPUT: Chỉ trả về JSON thuần túy, không dùng markdown (```json).
    QUY TẮC QUAN TRỌNG VỀ XỬ LÝ NGỮ CẢNH (CONTEXT MAPPING):
    Nếu trong lịch sử hội thoại (message của assistant) có chứa danh sách sách gợi ý (thường nằm trong khối [SYSTEM_CONTEXT_DATA]), bạn PHẢI thực hiện mapping:

    1. Mapping theo thứ tự: Nếu user nói "lấy cuốn 1", "cuốn số 2" -> Hãy lấy "title" của cuốn sách tương ứng trong danh sách đó điền vào "book".
    2. Mapping theo tên tắt: Nếu user nói "cuốn Azkaban", "cuốn Hòn đá" -> Hãy tìm trong danh sách gợi ý xem có cuốn nào chứa từ khóa đó không. Nếu có, HÃY DÙNG TÊN ĐẦY ĐỦ của sách đó (Ví dụ: "Harry Potter và Hòn đá phù thủy").
    3. Ưu tiên Context: Luôn ưu tiên tên sách có trong Context hơn là text thô user nhập.
    4. Nếu history có thông tin đơn hàng thì GIỮ NGUYÊN context đơn hàng đó cho các câu hỏi có liên quan sau đó, đến khi được cung cấp 'phone' khác (đơn hàng khác).
    ------------------------------------------------------------------

    VÍ DỤ 1 (Mapping tên tắt):
    History (Bot): "Có 2 cuốn: 1. Harry Potter và Hòn đá phù thủy, 2. Harry Potter và Phòng chứa bí mật"
    User: "Lấy cuốn hòn đá nha"
    Output: {
      "intent": "place_order",
      "entities": { "book_keywords": [{ "book": "Harry Potter và Hòn đá phù thủy", "quantity": 1 }] }
    }

    VÍ DỤ 2 (Mapping số thứ tự):
    History (Bot): [List sách...]
    User: "cho mình cuốn thứ 2 và cuốn Dune"
    Output: {
      "intent": "place_order",
      "entities": { "book_keywords": [
          { "book": "Harry Potter và Phòng chứa bí mật", "quantity": 1 },  <-- Lấy từ context
          { "book": "Dune", "quantity": 1 }                                <-- Sách mới
      ]}
    }
    """
    contents = []
    for msg in recent_history:
        role = "user" if msg['role'] == 'user' else 'model'
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg['content'])]
            )
        )
    contents.append(
        types.Content(
            role='user',
            parts=[types.Part.from_text(text=user_input)]
        )
    )

    try:
        response = client.models.generate_content(
            model = 'gemini-flash-latest',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0
            )
        )

        return json.loads(response.text)
    except Exception as e:
        print(f"❌ NLU Error (Google GenAI): {e}")
        return {
            "intent": "other", 
            "entities": {
                "book_keywords": [], "filters": {}, "customer_info": {}
            }
        }
