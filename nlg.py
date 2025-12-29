# Dựa trên lịch sử trò chyện gần đó (6 câu gần nhất) + Data truy vấn được + current_query để gen câu trả lời

import json
import os
from google import genai
from google.genai import types
from config import GOOGLE_API_KEY, STORE_INFO, ORDER_STATUS_MAP

client = genai.Client(
    api_key=GOOGLE_API_KEY
    )

def generate_response(user_input, data_context, intent):
    data_str = "Data not found!"

    if data_context:
        data_str = json.dumps(data_context, ensure_ascii=False)
    
    system_prompt = f"""
    Bạn là nhân viên bán sách tại: {STORE_INFO}
    Nhiệm vụ: Trả lời khách hàng dựa trên dữ liệu hệ thống cung cấp dưới đây.

    INTENT HIỆN TẠI: {intent}

    DỮ LIỆU TỪ DATABASE:
    {data_str}

    BẢNG MÃ TRẠNG THÁI ĐƠN HÀNG (Nếu cần):
    {json.dumps(ORDER_STATUS_MAP, ensure_ascii=False)}

    HƯỚNG DẪN TRẢ LỜI:
    1. Giọng điệu: Thân thiện, ngắn gọn, chuyên nghiệp.
    2. Nếu intent là 'search_book' hoặc 'recommend_book':
        - Nếu có sách: Chỉ liệt kê tên sách, tác giả và GIÁ TIỀN (format 100.000VND); tối đa 5 sách phù hợp nhất.
        - Nếu data rỗng: Xin lỗi và gợi ý tìm từ khóa khác hoặc bỏ bớt lọc giá.
    3. Nếu intent là 'order_management':
        - Báo rõ trạng thái đơn hàng bằng tiếng Việt.
    4. KHÔNG ĐƯỢC bịa ra sách không có trong DATABASE.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.5 #Mức độ sáng tạo của chatbot
            )
        )
        return response.text
    
    except Exception as e:
        print(f"❌ NLG Error (GenAI): {e}")
        return "Xin lỗi, hệ thống đang bận, bạn thử lại sau chút nhé."
