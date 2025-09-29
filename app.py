# app.py

import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import chatbot as bot

# Tải các biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')

@app.route("/")
def index():
    # Khởi tạo session cho người dùng mới
    if "chat_history" not in session:
        # <<< BẮT ĐẦU THAY ĐỔI
        initial_message = "Book store xin chào! Tôi có thể giúp gì cho bạn?"
        session["chat_history"] = [{"role": "model", "parts": [initial_message]}]
        # KẾT THÚC THAY ĐỔI >>>
        
        session["order_state"] = {
            "cart": [], "customer_name": None, "phone": None,
            "address": None, "confirming": False, "total_price": 0
        }
        session["last_query_result"] = None
        
    # Luôn truyền lịch sử chat cho template để hiển thị
    return render_template("index.html", chat_history=session["chat_history"])

# Route API để xử lý tin nhắn chat
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Lấy trạng thái từ session
    chat_history = session.get("chat_history", [])
    order_state = session.get("order_state", {})
    last_query_result = session.get("last_query_result")

    def reset_order_state():
        return {
            "cart": [], "customer_name": None, "phone": None,
            "address": None, "confirming": False, "total_price": 0
        }

    final_answer = ""
    # Logic xử lý chính, tương tự hàm main() cũ
    if order_state.get("confirming"):
        intent = bot.classify_intent(user_input, chat_history)
        print(f"DEBUG (Confirming): Intent -> {intent}")

        if intent == "confirm_order":
            try:
                for item in order_state['cart']:
                    res = bot.execute_sql_query("SELECT book_id FROM Books WHERE title = ?", (item['actual_title'],))
                    book_id = res["data"][0][0]
                    insert_sql = "INSERT INTO Orders (customer_name, phone, address, book_id, quantity, status) VALUES (?, ?, ?, ?, ?, ?)"
                    params = (
                        order_state["customer_name"], order_state["phone"], order_state["address"],
                        book_id, item["quantity"], "Pending"
                    )
                    bot.execute_sql_query(insert_sql, params)
                
                for item in order_state['cart']:
                    update_sql = "UPDATE Books SET stock = stock - ? WHERE title = ?"
                    bot.execute_sql_query(update_sql, (item['quantity'], item['actual_title']))
                
                final_answer = "Đặt hàng thành công! Cảm ơn bạn đã mua sách. Tôi có thể giúp gì khác cho bạn không?"
                order_state = reset_order_state()

            except Exception as e:
                final_answer = f"Xin lỗi, đã có lỗi xảy ra khi xử lý đơn hàng: {e}"
                order_state = reset_order_state()

        elif intent == "edit_order":
            order_state["confirming"] = False
            final_answer = bot.handle_ordering(user_input, order_state, chat_history, last_query_result)
        else: # Mặc định là cancel
            order_state = reset_order_state()
            final_answer = "Đã hủy đơn hàng. Tôi có thể giúp gì khác cho bạn không?"

    else:
        intent = bot.classify_intent(user_input, chat_history)
        print(f"DEBUG: Intent -> {intent}")
        if intent == "chitchat":
            final_answer = bot.handle_chitchat(user_input)
            last_query_result = None
        elif intent == "query_books":
            final_answer, sql_result = bot.handle_query_books(user_input, chat_history)
            if sql_result and "error" not in sql_result:
                last_query_result = sql_result
        elif intent == "reconsider_order":
            final_answer = bot.handle_reconsider_order(user_input, order_state)
        elif intent in ["order_book", "edit_order", "confirm_order"]:
            final_answer = bot.handle_ordering(user_input, order_state, chat_history, last_query_result)
        else:
            final_answer = "Xin lỗi, tôi chưa hiểu ý của bạn. Bạn muốn hỏi về sách, đặt hàng hay trò chuyện?"

    # Cập nhật lại session với trạng thái mới
    chat_history.append({"role": "user", "parts": [user_input]})
    chat_history.append({"role": "model", "parts": [final_answer]})
    session["chat_history"] = chat_history
    session["order_state"] = order_state
    session["last_query_result"] = last_query_result

    # Trả lời về cho frontend
    return jsonify({"response": final_answer})

if __name__ == "__main__":
    app.run(debug=True)

