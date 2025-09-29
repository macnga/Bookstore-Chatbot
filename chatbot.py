# chatbot_logic.py

import sqlite3
import google.generativeai as genai
import json
import re
import os
from thefuzz import process

# Lấy API key từ biến môi trường
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("models/gemini-2.5-flash")

def execute_sql_query(sql_query, params=()):
    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query, params)
        if sql_query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()
            if not rows:
                return {"message": "Data not found!"}
            return {"column": column_names, "data": rows}
        else:
            conn.commit()
            conn.close()
            return {"message": "Done successfully!"}
    except Exception as e:
        conn.close()
        return {"error": str(e)}


def classify_intent(user_input, chat_history):
    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])
    prompt = f"""
    Dựa vào lịch sử trò chuyện và tin nhắn mới nhất của người dùng, hãy phân loại ý định của họ thành một trong các loại sau:
    'chitchat', 'query_books', 'order_book', 'confirm_order', 'cancel_order', 'edit_order', 'reconsider_order'.
    Chỉ trả về MỘT TỪ duy nhất là tên của ý định.
    Lịch sử trò chuyện:
    {history_str}
    Tin nhắn mới nhất của người dùng: "{user_input}"
    """
    response = model.generate_content(prompt)
    return response.text.strip().lower()

def handle_chitchat(user_input):
    prompt = f"""
    Bạn là một trợ lý bán sách thân thiện.
    Hãy trả lời tin nhắn của khách hàng một cách tự nhiên và **ngắn gọn trong tối đa 2 câu**.
    Khách hàng nói: '{user_input}'
    """
    response = model.generate_content(prompt)
    return response.text

_VN_NUMBER_MAP = {
    "một": 1, "mot": 1, "hai": 2, "ba": 3, "bốn": 4, "bon": 4, "tư": 4,
    "năm": 5, "nam": 5, "sáu": 6, "sau": 6, "bảy": 7, "bay": 7,
    "tám": 8, "tam": 8, "chín": 9, "chin": 9, "mười": 10, "muoi": 10
}

def extract_quantity_from_text(text):
    if not text:
        return 1
    s = str(text).lower().strip()
    s_clean = re.sub(r"[^\w\s]", " ", s)
    for word, val in _VN_NUMBER_MAP.items():
        if re.search(r"\b" + re.escape(word) + r"\b", s_clean):
            return val
    m = re.search(r"\b(\d{1,3})\b", s_clean)
    if m:
        return int(m.group(1))
    return 1

DATABASE_SCHEMA = """
Table Books có các cột sau: book_id (INTEGER, PRIMARY KEY), title (TEXT), author (TEXT), price (REAL), stock (INTEGER), category (TEXT).
Table Orders có các cột sau: order_id (INTEGER, PRIMARY KEY), customer_name (TEXT), phone (TEXT), address (TEXT), book_id (INTEGER), quantity (INTEGER), status (TEXT).
"""

def get_database_context():
    all_titles_res = execute_sql_query("SELECT DISTINCT title FROM Books")
    all_categories_res = execute_sql_query("SELECT DISTINCT category FROM Books")
    all_authors_res = execute_sql_query("SELECT DISTINCT author FROM Books")

    db_titles = [row[0] for row in all_titles_res.get('data', [])]
    db_authors = [row[0] for row in all_authors_res.get('data', [])]
    db_categories = [row[0] for row in all_categories_res.get('data', [])]

    context = (
        f"DANH SÁCH TÊN SÁCH HIỆN CÓ:\n{', '.join(db_titles)}\n\n"
        f"DANH SÁCH TÁC GIẢ HIỆN CÓ:\n{', '.join(db_authors)}\n\n"
        f"DANH SÁCH THỂ LOẠI HIỆN CÓ:\n{', '.join(db_categories)}"
    )
    return context

def handle_query_books(user_input, chat_history):
    db_context = get_database_context()
    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])

    sql_prompt = f"""
    Bạn là một chuyên gia SQL. Nhiệm vụ của bạn là chuyển câu hỏi của người dùng thành một câu lệnh SQL chính xác dựa trên CSDL và ngữ cảnh được cung cấp.
    **QUAN TRỌNG**: Nếu thấy người dùng gõ sai chính tả một tên sách hoặc thể loại, hãy tự động sửa nó thành tên đúng nhất có trong danh sách ngữ cảnh dưới đây khi tạo câu lệnh SQL.
    **Ngữ cảnh từ Cơ sở dữ liệu:**
    {db_context}
    **Cấu trúc CSDL:**
    {DATABASE_SCHEMA}
    **Lịch sử trò chuyện:**
    {history_str}
    **Câu hỏi của người dùng:** "{user_input}"
    **Câu lệnh SQL (chỉ trả về mã SQL):**
    """

    sql_response = model.generate_content(sql_prompt)
    generated_sql = sql_response.text.replace("```sql", "").replace("```", "").strip()
    print(f"DEBUG: SQL -> {generated_sql}")

    sql_result = execute_sql_query(generated_sql)
    print(f"DEBUG: SQL Result -> {sql_result}")

    final_prompt = f"""
    Bạn là trợ lý bán sách. Dựa vào câu hỏi, lịch sử và kết quả SQL, hãy trả lời khách hàng một cách thân thiện và đầy đủ.
    Lịch sử: {history_str}
    Câu hỏi: "{user_input}"
    Kết quả SQL: {json.dumps(sql_result, ensure_ascii=False)}
    Câu trả lời:
    """
    final_response = model.generate_content(final_prompt)
    return final_response.text, sql_result

def format_history_for_prompt(chat_history):
    return "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])

def handle_ordering(user_input, order_state, chat_history, last_query_result):
    formatted_last_query = "Không có"
    if last_query_result and last_query_result.get("data"):
        items = [dict(zip(last_query_result['column'], row)) for row in last_query_result['data']]
        formatted_last_query = json.dumps(items, ensure_ascii=False, indent=2)

    extract_prompt = f"""
    Bạn là một trợ lý thông minh. Nhiệm vụ của bạn là trích xuất thông tin đặt hàng từ tin nhắn của người dùng.
    **Ngữ cảnh bổ sung (Kết quả tra cứu gần nhất của người dùng):**
    ```json
    {formatted_last_query}
    ```
    **Lịch sử hội thoại:**
    {format_history_for_prompt(chat_history)}
    **Tin nhắn mới nhất của người dùng:** "{user_input}"
    **YÊU CẦU:**
    Dựa vào tin nhắn mới nhất, lịch sử và **ngữ cảnh bổ sung** trên, trích xuất các thông tin sau và trả về dưới dạng JSON:
    - customer_name (string or null)
    - phone (string or null)
    - address (string or null)
    - books (một LIST các object, mỗi object có 'title' và 'quantity').
    **QUAN TRỌNG:** Nếu tin nhắn mới nhất không đề cập đến tên sách cụ thể (ví dụ: "cuốn đó", "lấy cho mình cuốn đầu tiên"), hãy **suy luận tên sách** từ **Ngữ cảnh bổ sung**.
    JSON:
    """
    info_response = model.generate_content(extract_prompt)
    try:
        cleaned_json_text = info_response.text.replace("```json", "").replace("```", "").strip()
        extracted_info = json.loads(cleaned_json_text)
        if extracted_info.get("customer_name"): order_state["customer_name"] = extracted_info["customer_name"]
        if extracted_info.get("phone"): order_state["phone"] = extracted_info["phone"]
        if extracted_info.get("address"): order_state["address"] = extracted_info["address"]

        if extracted_info.get("books"):
            for new_book in extracted_info.get("books"):
                requested_title = new_book.get("title")
                requested_qty = extract_quantity_from_text(new_book.get("quantity"))
                if not requested_title: continue
                found_in_cart = False
                for cart_item in order_state["cart"]:
                    if requested_title.lower() in cart_item.get("title", "").lower():
                        cart_item["quantity"] = requested_qty
                        found_in_cart = True
                        break
                if not found_in_cart:
                    order_state["cart"].append({"title": requested_title, "quantity": requested_qty})

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"DEBUG: Lỗi trích xuất JSON: {e}")
        return "Xin lỗi, tôi chưa hiểu rõ yêu cầu của bạn. Bạn vui lòng cho biết tên sách và số lượng muốn mua được không ạ?"

    if not order_state["cart"]:
        return "Bạn muốn mua cuốn sách nào ạ?"

    total = 0
    cart_details_text = []
    
    all_titles_res = execute_sql_query("SELECT title FROM Books")
    if "error" in all_titles_res or "message" in all_titles_res:
        return "Xin lỗi, không thể kết nối tới kho sách lúc này."
    db_titles = [row[0] for row in all_titles_res['data']]

    SCORE_THRESHOLD = 75

    for item in order_state["cart"]:
        item_title_lower = item['title'].lower().strip()
        best_match = process.extractOne(item_title_lower, db_titles, score_cutoff=SCORE_THRESHOLD)
        if not best_match:
            return f"Xin lỗi, không tìm thấy sách nào có tên giống '{item['title']}' trong kho. Bạn vui lòng kiểm tra lại chính tả nhé."

        found_title = best_match[0]
        res = execute_sql_query("SELECT price, stock FROM Books WHERE title = ?", (found_title,))
        price, stock = res["data"][0]
        qty = item["quantity"]

        if qty > stock:
            return f"Xin lỗi, cuốn '{found_title}' chỉ còn {stock} cuốn, không đủ {qty} cuốn bạn yêu cầu."

        total += price * qty
        item['actual_title'] = found_title
        item['price'] = price
        cart_details_text.append(f"- {qty} cuốn '{found_title}' (Đơn giá: {price:,.0f} VNĐ)")

    order_state["total_price"] = total
    cart_summary = "\n".join(cart_details_text)

    missing = []
    if not order_state.get("customer_name"): missing.append("tên")
    if not order_state.get("phone"): missing.append("số điện thoại")
    if not order_state.get("address"): missing.append("địa chỉ")

    if missing:
        return (f"Đơn hàng của bạn gồm:\n{cart_summary}\n"
                f"Tổng cộng: {total:,.0f} VNĐ.\n"
                f"Vui lòng cho tôi biết {' và '.join(missing)} của bạn.")

    order_state["confirming"] = True
    summary = (f"Vui lòng xác nhận lại thông tin đơn hàng của bạn:\n"
               f"{cart_summary}\n"
               f"- Tổng cộng: {total:,.0f} VNĐ\n"
               f"- Tên người nhận: {order_state['customer_name']}\n"
               f"- Số điện thoại: {order_state['phone']}\n"
               f"- Địa chỉ giao hàng: {order_state['address']}\n\n"
               f'Thông tin đã chính xác chưa ạ? (trả lời "chính xác", "sửa thông tin" hoặc "hủy")')
    return summary

def handle_reconsider_order(user_input, order_state):
    return "Dạ em hiểu ạ. Không biết mình muốn giảm số lượng hay tìm một cuốn sách khác có giá tốt hơn ạ?"
