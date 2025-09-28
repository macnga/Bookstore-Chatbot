from flask import Flask, request, jsonify, render_template, session
import os
import chatbot
from copy import deepcopy

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_session_state():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'order_state' not in session:
        session['order_state'] = {
            "cart": [], "customer_name": None, "phone": None,
            "address": None, "confirming": False, "total_price": 0
        }
    if 'pending_confirmation' not in session:
        session['pending_confirmation'] = None

@app.route('/')
def index():
    init_session_state()
    chat_history = session.get('chat_history', [])
    if not chat_history:  # nếu lần đầu vào, thêm lời chào
        greeting = "Book store xin chào quý khách! Tôi có thể giúp gì cho bạn?"
        chat_history.append({"role": "model", "parts": [greeting]})
        session['chat_history'] = chat_history
    return render_template('index.html')

@app.route('/history')
def history():
    init_session_state()
    return jsonify({"history": session.get("chat_history", [])})

def reset_order_state():
    return {
        "cart": [], "customer_name": None, "phone": None,
        "address": None, "confirming": False, "total_price": 0
    }

def classify_confirmation(user_input):
    text = user_input.strip().lower()
    affirm_keywords = ["đúng", "chính xác", "chuẩn rồi", "ok", "phải", "ừ", "đúng vậy"]
    neg_keywords = ["không", "sai", "không phải", "chưa đúng", "nhầm"]
    if any(k in text for k in affirm_keywords):
        return "affirm"
    if any(k in text for k in neg_keywords):
        return "neg"
    return "other"

@app.route('/chat', methods=['POST'])
def chat():
    init_session_state()

    user_input = request.json.get('message', '')
    if user_input is None:
        return jsonify({"reply": "Invalid input."})
    user_input = str(user_input).strip()

    chat_history = session.get('chat_history', [])
    order_state = session.get('order_state', {})
    pending = session.get('pending_confirmation')

    # 1) Nếu đang chờ xác nhận best match
    if pending:
        conf = classify_confirmation(user_input)
        if conf == "affirm":
            book = pending['book_info']
            session['pending_confirmation'] = None
            reply = f"Có '{book['title']}' ({book['price']:,.0f} VND, còn {book['stock']} cuốn)."
        elif conf == "neg":
            session['pending_confirmation'] = None
            reply = "Ok, bạn có thể nhập lại tên sách rõ hơn giúp mình nhé."
        else:
            # Nếu người dùng nhập câu khác → coi như yêu cầu mới, bỏ pending
            session['pending_confirmation'] = None
            reply = None
        if reply:
            chat_history.append({"role": "user", "parts": [user_input]})
            chat_history.append({"role": "model", "parts": [reply]})
            session['chat_history'] = chat_history
            session['order_state'] = order_state
            return jsonify({"reply": reply})

    # 2) Nếu đang trong bước xác nhận order
    if order_state.get("confirming"):
        intent = chatbot.classify_intent(user_input, chat_history)
        if intent == "confirm_order":
            try:
                for item in order_state['cart']:
                    res = chatbot.execute_sql_query("SELECT book_id FROM Books WHERE title = ?", (item['actual_title'],))
                    book_id = res["data"][0][0]
                    params = (order_state["customer_name"], order_state["phone"], order_state["address"], book_id, item["quantity"], "Pending")
                    chatbot.execute_sql_query("INSERT INTO Orders (customer_name, phone, address, book_id, quantity, status) VALUES (?, ?, ?, ?, ?, ?)", params)
                    chatbot.execute_sql_query("UPDATE Books SET stock = stock - ? WHERE title = ?", (item['quantity'], item['actual_title']))
                final_answer = "Đặt hàng thành công! Cảm ơn bạn đã mua sách."
                order_state = reset_order_state()
            except Exception as e:
                final_answer = f"Xin lỗi, đã có lỗi xảy ra: {e}"
                order_state = reset_order_state()
        elif intent == "edit_order":
            order_state["confirming"] = False
            final_answer = chatbot.handle_ordering(user_input, order_state, chat_history)
        else:
            order_state = reset_order_state()
            final_answer = "Đã hủy đơn hàng. Tôi có thể giúp gì khác cho bạn không?"
        chat_history.append({"role": "user", "parts": [user_input]})
        chat_history.append({"role": "model", "parts": [final_answer]})
        session['chat_history'] = chat_history
        session['order_state'] = order_state
        return jsonify({"reply": final_answer})

    # 3) Bình thường
    intent = chatbot.classify_intent(user_input, chat_history)
    if intent == "chitchat":
        reply = chatbot.handle_chitchat(user_input)
    elif intent == "query_books":
        reply = chatbot.handle_query_books(user_input, chat_history)
        mod_pending = getattr(chatbot, "pending_confirmation", None)
        if mod_pending and mod_pending.get("title"):
            session['pending_confirmation'] = deepcopy(mod_pending)
            chatbot.pending_confirmation = {"title": None, "book_info": None}
    elif intent == "reconsider_order":
        reply = chatbot.handle_reconsider_order(user_input, order_state)
    elif intent in ["order_book", "edit_order", "confirm_order"]:
        reply = chatbot.handle_ordering(user_input, order_state, chat_history)
    else:
        reply = "Xin lỗi, tôi chưa hiểu ý của bạn. Bạn muốn hỏi về sách, đặt hàng hay trò chuyện?"

    chat_history.append({"role": "user", "parts": [user_input]})
    chat_history.append({"role": "model", "parts": [reply]})
    session['chat_history'] = chat_history
    session['order_state'] = order_state

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
