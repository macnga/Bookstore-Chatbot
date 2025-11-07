# app.py
#
# Modified to:
# - Queue incoming user messages per-session.
# - Debounce incoming messages: wait 5s after the last received message, then
#   concatenate all queued messages and process them as a single prompt.
# - Limit queued messages to 10 per-session.
# - Allow users to send messages even while an API call is in progress.
# - Provide an endpoint for the frontend to fetch the current server-side chat history.
#
# Notes:
# - We keep a server-side sessions_state dict keyed by a session_id stored in the
#   Flask session cookie. This is required because background threads cannot access
#   Flask's `session` object outside a request context.
# - The frontend must poll /updates to retrieve model responses produced asynchronously.
#   (You can wire this to a periodic Ajax / fetch call or use websockets/SSE for push.)
# - The queue is debounced: each new request resets a 5-second timer. When that timer
#   fires with no new requests, all queued messages at that moment are concatenated and
#   processed in the background.
# - While processing, new messages are allowed and go into a fresh queue for the next batch.
#
import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import chatbot as bot

# Tải các biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')

# Server-side state per-session_id (because background threads cannot access Flask session)
# Structure:
# sessions_state[session_id] = {
#   "queue": [str, ...],
#   "timer": threading.Timer or None,
#   "lock": threading.Lock(),
#   "chat_history": [...],  # same structure as before
#   "order_state": {...},
#   "last_query_result": ...,
#   "processing": False
# }
sessions_state = {}
# Maximum queued messages allowed before user must wait for batch to be processed
MAX_QUEUE_SIZE = 10
# Debounce delay (seconds)
DEBOUNCE_SECONDS = 5.0

def init_server_session(session_id):
    """Initialize server-side state for a new session_id."""
    if session_id in sessions_state:
        return sessions_state[session_id]

    initial_message = "Book store xin chào! Tôi có thể giúp gì cho bạn?"
    state = {
        "queue": [],
        "timer": None,
        "lock": threading.Lock(),
        "chat_history": [{"role": "model", "parts": [initial_message]}],
        "order_state": {
            "cart": [], "customer_name": None, "phone": None,
            "address": None, "confirming": False, "total_price": 0
        },
        "last_query_result": None,
        "processing": False
    }
    sessions_state[session_id] = state
    return state

def _reset_order_state_struct():
    return {
        "cart": [], "customer_name": None, "phone": None,
        "address": None, "confirming": False, "total_price": 0
    }

def _process_batch_in_thread(session_id, batch_messages):
    """Run actual processing in a background thread (so Timer thread isn't blocked)."""
    thread = threading.Thread(target=_process_batch, args=(session_id, batch_messages), daemon=True)
    thread.start()

def _process_batch(session_id, batch_messages):
    """Take a list of user messages (strings), concatenate them and run the bot logic.
    Update the server-side chat_history / order_state accordingly.
    """
    state = sessions_state.get(session_id)
    if state is None:
        return

    # Set processing flag (others can still enqueue new messages)
    with state["lock"]:
        state["processing"] = True

    # Concatenate messages into a single prompt
    concatenated = "\n".join(batch_messages).strip()
    if not concatenated:
        # Nothing to do
        with state["lock"]:
            state["processing"] = False
        return

    # Use a copy of current state to operate on and update in the end
    chat_history = state.get("chat_history", [])
    order_state = state.get("order_state", {})
    last_query_result = state.get("last_query_result", None)

    # The core logic is the same as previous synchronous /chat handler, but
    # applied to the concatenated input.
    user_input = concatenated
    final_answer = ""

    try:
        if order_state.get("confirming"):
            intent = bot.classify_intent(user_input, chat_history)
            print(f"DEBUG (Confirming, background): Intent -> {intent}")

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
                    order_state = _reset_order_state_struct()

                except Exception as e:
                    final_answer = f"Xin lỗi, đã có lỗi xảy ra khi xử lý đơn hàng: {e}"
                    order_state = _reset_order_state_struct()

            elif intent == "edit_order":
                order_state["confirming"] = False
                final_answer = bot.handle_ordering(user_input, order_state, chat_history, last_query_result)
            else:  # Mặc định là cancel
                order_state = _reset_order_state_struct()
                final_answer = "Đã hủy đơn hàng. Tôi có thể giúp gì khác cho bạn không?"

        else:
            intent = bot.classify_intent(user_input, chat_history)
            print(f"DEBUG (background): Intent -> {intent}")
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
    except Exception as e:
        final_answer = f"Xin lỗi, đã có lỗi nội bộ khi xử lý: {e}"

    # Append the user messages and model response to server-side chat_history
    # Note: we append the concatenated user input as a single user message
    with state["lock"]:
        chat_history.append({"role": "user", "parts": [concatenated]})
        chat_history.append({"role": "model", "parts": [final_answer]})

        # Update order_state and last_query_result back to server state
        state["chat_history"] = chat_history
        state["order_state"] = order_state
        state["last_query_result"] = last_query_result

        # Batch processed -> ensure processing flag false
        state["processing"] = False
        # Note: we do NOT clear any messages that arrived after the snapshot was taken;
        # they remain in state["queue"] for the next batch.

    print(f"DEBUG: Processed batch for session {session_id}. Batch size: {len(batch_messages)}")

def _timer_callback(session_id):
    """Timer callback called when debounce delay elapses with no new messages.
    This will snapshot the current queue, clear those items from queue, and process them.
    """
    state = sessions_state.get(session_id)
    if state is None:
        return

    # Snapshot and clear queued messages for this batch
    with state["lock"]:
        queued = state["queue"][:]
        state["queue"] = []
        # Also clear the timer ref (we are in its callback)
        state["timer"] = None

    if not queued:
        return

    # Start processing in a separate thread
    _process_batch_in_thread(session_id, queued)

@app.route("/")
def index():
    # Khởi tạo session cho người dùng mới
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]
    # Ensure server-side state exists and is initialized
    init_server_session(session_id)

    # Luôn truyền lịch sử chat cho template để hiển thị
    # NOTE: This renders from the server-side sessions_state chat_history. The frontend
    # can also poll /updates to get new updates asynchronously.
    server_state = sessions_state.get(session_id, {})
    return render_template("index.html", chat_history=server_state.get("chat_history", []))


# Route API để xử lý tin nhắn chat (queues the message, debounces processing)
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if user_input is None:
        return jsonify({"error": "No message provided"}), 400

    # Ensure session_id exists
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]

    state = init_server_session(session_id)

    with state["lock"]:
        # Enforce max queued messages
        if len(state["queue"]) >= MAX_QUEUE_SIZE:
            return jsonify({
                "error": "Bạn đã gửi tối đa 10 request liên tiếp. Vui lòng đợi kết quả."
            }), 429

        # Append to queue
        state["queue"].append(user_input)

        # Reset debounce timer: cancel old timer (if any), and start a new one
        if state["timer"] is not None:
            try:
                state["timer"].cancel()
            except Exception:
                pass

        timer = threading.Timer(DEBOUNCE_SECONDS, _timer_callback, args=(session_id,))
        state["timer"] = timer
        timer.daemon = True
        timer.start()

        queued_count = len(state["queue"])
        processing = state["processing"]

    # Immediately return acknowledgement to the client. The actual bot response will be
    # produced asynchronously after the debounce delay and can be fetched from /updates.
    return jsonify({
        "status": "queued",
        "queued": queued_count,
        "processing": processing,
        "message": f"Yêu cầu đã được thêm vào hàng đợi. Hệ thống sẽ gom các yêu cầu trong {DEBOUNCE_SECONDS} giây sau lần gửi cuối cùng."
    })


# Endpoint for frontend to fetch the current server-side chat_history (and some state)
# The frontend should poll this endpoint to retrieve responses produced asynchronously.
@app.route("/updates", methods=["GET"])
def updates():
    if "session_id" not in session:
        return jsonify({"error": "No session"}), 400
    session_id = session["session_id"]
    state = sessions_state.get(session_id)
    if state is None:
        return jsonify({"error": "Session not initialized"}), 400

    with state["lock"]:
        return jsonify({
            "chat_history": state.get("chat_history", []),
            "queue_length": len(state.get("queue", [])),
            "processing": state.get("processing", False)
        })


if __name__ == "__main__":
    # Note: In production, you should run Flask with a WSGI server (gunicorn/uvicorn).
    # Also be mindful: in multi-process deployments (multiple workers), in-memory
    # sessions_state won't be shared across workers. For multi-worker production
    # you must move sessions_state to a shared store (Redis, DB, etc.).
    app.run(debug=True)
