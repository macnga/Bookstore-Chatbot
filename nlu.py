# Thực hiện phân loại intent và trích xuất các thông tin cần thiết

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
