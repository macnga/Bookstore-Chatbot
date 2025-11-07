```python name=chatbot.py url=https://github.com/macnga/Bookstore-Chatbot/blob/main/chatbot.py
# chatbot.py
# Updated to:
# - Use OpenAI Python client.
# - Use gpt-3.5-turbo for internal tasks (intent classification, SQL generation, JSON extraction).
# - Use gpt-4o-mini for final responses that are printed to users.
#
# Notes:
# - Ensure OPENAI_API_KEY is set in environment.
# - Each DB access opens its own sqlite3 connection (connection-per-call) to be thread-safe.
# - All OpenAI calls go through call_chat_model helper which uses the OpenAI client.
# - Timeouts and basic error handling added; tune as needed.

import os
import sqlite3
import json
import re
from thefuzz import process
from pathlib import Path
import time

try:
    from openai import OpenAI
except Exception:
    # If OpenAI SDK not installed, raise helpful error at import-time
    raise RuntimeError("OpenAI Python SDK not found. Install with `pip install openai` or the appropriate package.")

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Do not fail hard here — functions will raise when trying to call API if key is missing.
    pass

# Initialize client
client = OpenAI(api_key=OPENAI_API_KEY)

# Model selection
CLASSIFY_MODEL = os.getenv("CLASSIFY_MODEL", "gpt-3.5-turbo")   # for classify/sql/extraction
FINAL_MODEL = os.getenv("FINAL_MODEL", "gpt-4o-mini")           # for final printed responses

# OpenAI call defaults
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "30"))


def _call_chat_model(model: str, messages: list, max_tokens: int = 512, temperature: float = 0.2):
    """
    Call the chat completions API via the SDK.
    messages: list of {"role": "...", "content": "..."}
    Returns string content from the first choice (or raises Exception).
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            request_timeout=OPENAI_TIMEOUT
        )
        # Newer OpenAI SDK returns choices -> first -> message -> content
        if resp and getattr(resp, "choices", None):
            first = resp.choices[0]
            # Some SDK shapes: choice.message.content or choice["message"]["content"]
            content = None
            if hasattr(first, "message") and isinstance(first.message, dict):
                content = first.message.get("content")
            elif hasattr(first, "message") and hasattr(first.message, "get"):
                content = first.message.get("content")
            else:
                # try dict access
                try:
                    content = first["message"]["content"]
                except Exception:
                    pass
            if content is None:
                # try text or other keys
                content = getattr(first, "text", None) or first.get("text", None)
            return content or ""
        # fallback: try to parse as dict
        try:
            data = resp.to_dict()
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message") or {}
                return msg.get("content") or choices[0].get("text") or ""
        except Exception:
            pass
        return ""
    except Exception as e:
        raise


def execute_sql_query(sql_query, params=()):
    """
    Execute a SQL statement on bookstore.db.
    Each call creates its own connection to be safe in multithreaded usage.
    """
    db_path = Path("bookstore.db")
    if not db_path.exists():
        return {"error": "Database file not found."}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query, params)
        if sql_query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()
            if not rows:
                return {"message": "Data not found!", "column": column_names, "data": []}
            return {"column": column_names, "data": rows}
        else:
            conn.commit()
            conn.close()
            return {"message": "Done successfully!"}
    except Exception as e:
        conn.close()
        return {"error": str(e)}


def classify_intent(user_input, chat_history):
    """
    Use CLASSIFY_MODEL (gpt-3.5-turbo) to return a single-word intent.
    Possible outputs: 'chitchat', 'query_books', 'order_book', 'confirm_order', 'cancel_order', 'edit_order', 'reconsider_order'.
    Returns lowercase one-word string (or 'chitchat' fallback).
    """
    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])
    system = (
        "You are a Vietnamese intent classifier for a bookstore assistant. "
        "Based on the conversation history and latest user message, return EXACTLY ONE word "
        "that indicates the user's intent from the following set: "
        "chitchat, query_books, order_book, confirm_order, cancel_order, edit_order, reconsider_order. "
        "Return only the intent token, nothing else."
    )
    user = f"History:\n{history_str}\n\nUser's latest message: \"{user_input}\""
    try:
        resp_text = _call_chat_model(
            model=CLASSIFY_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=16,
            temperature=0.0
        )
        if not resp_text:
            return "chitchat"
        # sanitize to single token
        intent = resp_text.strip().split()[0].strip().lower()
        # Normalize common punctuation
        intent = re.sub(r"[^a-z_]", "", intent)
        allowed = {"chitchat", "query_books", "order_book", "confirm_order", "cancel_order", "edit_order", "reconsider_order"}
        if intent not in allowed:
            return "chitchat"
        return intent
    except Exception:
        return "chitchat"


def handle_chitchat(user_input, chat_history=None):
    """
    Produce a short natural chitchat reply for the user using FINAL_MODEL (gpt-4o-mini).
    """
    prompt = (
        "Bạn là một trợ lý bán sách thân thiện. Trả lời ngắn gọn và tự nhiên (tối đa 2 câu) cho khách hàng.\n"
        f"Khách hàng: {user_input}\n"
    )
    try:
        resp_text = _call_chat_model(
            model=FINAL_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.6
        )
        return resp_text or "Xin lỗi, tôi không rõ. Bạn vui lòng nói lại được không?"
    except Exception as e:
        return f"Xin lỗi, có lỗi khi tạo phản hồi: {e}"


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
Table Books has columns: book_id (INTEGER, PRIMARY KEY), title (TEXT), author (TEXT), price (REAL), stock (INTEGER), category (TEXT).
Table Orders has columns: order_id (INTEGER, PRIMARY KEY), customer_name (TEXT), phone (TEXT), address (TEXT), book_id (INTEGER), quantity (INTEGER), status (TEXT).
"""


def get_database_context():
    all_titles_res = execute_sql_query("SELECT DISTINCT title FROM Books")
    all_categories_res = execute_sql_query("SELECT DISTINCT category FROM Books")
    all_authors_res = execute_sql_query("SELECT DISTINCT author FROM Books")

    db_titles = [row[0] for row in all_titles_res.get('data', [])] if all_titles_res.get('data') else []
    db_authors = [row[0] for row in all_authors_res.get('data', [])] if all_authors_res.get('data') else []
    db_categories = [row[0] for row in all_categories_res.get('data', [])] if all_categories_res.get('data') else []

    context = (
        f"DANH SÁCH TÊN SÁCH HIỆN CÓ:\n{', '.join(db_titles)}\n\n"
        f"DANH SÁCH TÁC GIẢ HIỆN CÓ:\n{', '.join(db_authors)}\n\n"
        f"DANH SÁCH THỂ LOẠI HIỆN CÓ:\n{', '.join(db_categories)}"
    )
    return context


def handle_query_books(user_input, chat_history):
    """
    1) Use CLASSIFY_MODEL to generate SQL (only SQL code).
    2) Execute SQL locally.
    3) Use FINAL_MODEL to craft the final user-facing answer using SQL results.
    Returns: (final_answer: str, sql_result: dict)
    """
    db_context = get_database_context()
    history_str = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])

    sql_prompt = (
        "Bạn là một chuyên gia SQL. Nhiệm vụ: chuyển câu hỏi của người dùng thành một câu lệnh SQL chính xác. "
        "Chỉ trả về một câu lệnh SQL duy nhất (KHÔNG có văn bản khác). Nếu cần, sử dụng thông tin ngữ cảnh dưới đây.\n\n"
        f"Ngữ cảnh từ CSDL:\n{db_context}\n\n"
        f"Cấu trúc CSDL:\n{DATABASE_SCHEMA}\n\n"
        f"Lịch sử trò chuyện:\n{history_str}\n\n"
        f"Câu hỏi của người dùng: \"{user_input}\"\n\n"
        "CHỈ TRẢ VỀ MỘT CÂU LỆNH SQL."
    )

    try:
        generated_sql = _call_chat_model(
            model=CLASSIFY_MODEL,
            messages=[{"role": "user", "content": sql_prompt}],
            max_tokens=256,
            temperature=0.0
        )
        if not generated_sql:
            return ("Xin lỗi, tôi không thể tạo câu lệnh truy vấn. Bạn vui lòng diễn đạt lại.", {"error": "empty_sql"})
        # Clean up code fences if any
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
    except Exception as e:
        return (f"Xin lỗi, lỗi khi tạo SQL: {e}", {"error": str(e)})

    # Execute SQL
    try:
        sql_result = execute_sql_query(generated_sql)
    except Exception as e:
        sql_result = {"error": str(e)}

    # Final answer assembled by FINAL_MODEL
    final_prompt = (
        "Bạn là trợ lý bán sách. Dựa vào dữ liệu dưới đây, trả lời khách hàng một cách thân thiện và rõ ràng.\n\n"
        f"Lịch sử: {history_str}\n\n"
        f"Câu hỏi: {user_input}\n\n"
        f"Kết quả SQL (JSON-serializable): {json.dumps(sql_result, ensure_ascii=False)}\n\n"
        "Trả lời ngắn gọn, dễ hiểu, và nếu không có dữ liệu, nói rõ 'không tìm thấy'."
    )
    try:
        final_response = _call_chat_model(
            model=FINAL_MODEL,
            messages=[{"role": "user", "content": final_prompt}],
            max_tokens=300,
            temperature=0.4
        )
    except Exception as e:
        final_response = f"Xin lỗi, lỗi khi tạo phản hồi: {e}"

    return final_response, sql_result


def format_history_for_prompt(chat_history):
    return "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in chat_history])


def handle_ordering(user_input, order_state, chat_history, last_query_result):
    """
    1) Use CLASSIFY_MODEL to extract structured order info (JSON) from user_input.
    2) Update order_state based on extraction and DB lookup.
    3) Use FINAL_MODEL to generate a friendly confirmation / follow-up message for the user.
    Returns: final message string (to be printed).
    """
    formatted_last_query = "Không có"
    if last_query_result and last_query_result.get("data"):
        items = [dict(zip(last_query_result['column'], row)) for row in last_query_result['data']]
        formatted_last_query = json.dumps(items, ensure_ascii=False, indent=2)

    extract_prompt = (
        "Bạn là một trợ lý thông minh. Trích xuất thông tin đặt hàng từ tin nhắn của người dùng và trả về một JSON "
        "chứa: customer_name (string|null), phone (string|null), address (string|null), books (LIST of {title, quantity}).\n\n"
        f"Ngữ cảnh bổ sung (kết quả tra cứu gần nhất):\n{formatted_last_query}\n\n"
        f"Lịch sử:\n{format_history_for_prompt(chat_history)}\n\n"
        f"Tin nhắn: \"{user_input}\"\n\n"
        "TRẢ VỀ CHỈ MỘT ĐỐI TƯỢNG JSON."
    )
    try:
        extraction_text = _call_chat_model(
            model=CLASSIFY_MODEL,
            messages=[{"role": "user", "content": extract_prompt}],
            max_tokens=400,
            temperature=0.0
        )
        cleaned_json_text = extraction_text.replace("```json", "").replace("```", "").strip()
        extracted_info = json.loads(cleaned_json_text)
    except Exception:
        # fallback: do not modify order_state; ask for clarification
        return "Xin lỗi, tôi chưa hiểu. Bạn có thể cho biết tên sách và số lượng rõ hơn không?"

    # Update order_state
    if extracted_info.get("customer_name"):
        order_state["customer_name"] = extracted_info["customer_name"]
    if extracted_info.get("phone"):
        order_state["phone"] = extracted_info["phone"]
    if extracted_info.get("address"):
        order_state["address"] = extracted_info["address"]

    if extracted_info.get("books"):
        for new_book in extracted_info.get("books"):
            requested_title = new_book.get("title")
            requested_qty = extract_quantity_from_text(new_book.get("quantity"))
            if not requested_title:
                continue
            found_in_cart = False
            for cart_item in order_state["cart"]:
                if requested_title.lower() in cart_item.get("title", "").lower():
                    cart_item["quantity"] = requested_qty
                    found_in_cart = True
                    break
            if not found_in_cart:
                order_state["cart"].append({"title": requested_title, "quantity": requested_qty})

    if not order_state["cart"]:
        return "Bạn muốn mua cuốn sách nào ạ?"

    # Validate stock/prices and prepare summary (local logic)
    all_titles_res = execute_sql_query("SELECT title FROM Books")
    if "error" in all_titles_res:
        return "Xin lỗi, không thể kết nối tới kho sách lúc này."
    db_titles = [row[0] for row in all_titles_res.get('data', [])] if all_titles_res.get('data') else []

    SCORE_THRESHOLD = 75
    total = 0
    cart_details_text = []

    for item in order_state["cart"]:
        item_title_lower = item['title'].lower().strip()
        best_match = process.extractOne(item_title_lower, db_titles, score_cutoff=SCORE_THRESHOLD)
        if not best_match:
            return f"Xin lỗi, không tìm thấy sách nào có tên giống '{item['title']}' trong kho. Bạn vui lòng kiểm tra lại chính tả nhé."
        found_title = best_match[0]
        res = execute_sql_query("SELECT price, stock FROM Books WHERE title = ?", (found_title,))
        if "error" in res or not res.get("data"):
            return "Xin lỗi, lỗi tra cứu thông tin sách."
        price, stock = res["data"][0]
        qty = item["quantity"]
        if qty > stock:
            return f"Xin lỗi, cuốn '{found_title}' chỉ còn {stock} cuốn, không đủ {qty} cuốn bạn yêu cầu."
        total += price * qty
        item['actual_title'] = found_title
        item['price'] = price
        cart_details_text.append(f"- {qty} cuốn '{found_title}' (Đơn giá: {price:,.0f} VNĐ)")

    order_state["total_price"] = total

    missing = []
    if not order_state.get("customer_name"):
        missing.append("tên")
    if not order_state.get("phone"):
        missing.append("số điện thoại")
    if not order_state.get("address"):
        missing.append("địa chỉ")

    # Build the human-readable summary via FINAL_MODEL
    summary_text = (
        f"Đơn hàng gồm:\n{chr(10).join(cart_details_text)}\nTổng: {total:,.0f} VNĐ.\n"
        f"Tên người nhận: {order_state.get('customer_name') or 'Chưa có'}\n"
        f"SĐT: {order_state.get('phone') or 'Chưa có'}\n"
        f"Địa chỉ: {order_state.get('address') or 'Chưa có'}\n"
    )
    follow_up = ""
    if missing:
        follow_up = f"Vui lòng cung cấp {' và '.join(missing)} để hoàn tất đơn hàng."
    else:
        order_state["confirming"] = True
        follow_up = 'Thông tin đã chính xác chưa ạ? (trả lời "chính xác", "sửa thông tin" hoặc "hủy")'

    final_prompt = (
        "Bạn là trợ lý bán sách. Dựa vào thông tin sau, soạn một đoạn văn thân thiện, ngắn gọn để gửi cho khách hàng:\n\n"
        f"{summary_text}\n\n{follow_up}\n\n"
        "Đoạn trả lời nên lịch sự, rõ ràng và bỏ những chi tiết kĩ thuật."
    )
    try:
        final_response = _call_chat_model(
            model=FINAL_MODEL,
            messages=[{"role": "user", "content": final_prompt}],
            max_tokens=250,
            temperature=0.4
        )
    except Exception as e:
        final_response = summary_text + "\n" + follow_up

    return final_response


def handle_reconsider_order(user_input, order_state):
    """
    Use FINAL_MODEL to provide a friendly follow-up when user wants to reconsider an order.
    """
    prompt = (
        "Bạn là một trợ lý bán sách. Người dùng muốn xem xét lại đơn hàng. Trả lời ngắn gọn "
        f"với câu hỏi mở để hiểu họ muốn thay đổi gì: {user_input}"
    )
    try:
        resp = _call_chat_model(
            model=FINAL_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.5
        )
        return resp or "Dạ, bạn muốn thay đổi điều gì trong đơn hàng ạ?"
    except Exception:
        return "Dạ, bạn muốn thay đổi điều gì trong đơn hàng ạ?"
