"""# app.py
#
# Behavior:
# - Per-session logging persisted as a single JSON array file at logs/{session_id}.json
# - Events are appended atomically with a file lock to avoid corruption across threads.
# - Each event: { ts, type, payload }
# - The app keeps in-memory session state and logs for fast access and persists them to the backend JSON file.
# - Request handling: classify/sql in background pool, debounce, final LLM batch processing in background.
# - Non-streaming: LLM response is appended when backend receives it; frontend should poll /updates to get updates.

import os
import uuid
import threading
import time
import json
import concurrent.futures
from pathlib import Path
from tempfile import NamedTemporaryFile
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import chatbot as bot

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')

# In-memory per-session state (Note: not shared across processes; for production use Redis/DB)
sessions_state = {}
MAX_QUEUE_SIZE = 10
DEBOUNCE_SECONDS = 5.0

# ThreadPool for quick classify/sql tasks
CLASSIFY_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=8)
# ThreadPool for final LLM calls (fewer workers)
LLM_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# Logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_LOCK = threading.Lock()


def _log_file_path(session_id: str) -> Path:
    return LOG_DIR / f"{session_id}.json"


def _atomic_write_json(path: Path, data):
    # write to temp file then replace to avoid partial files
    dirpath = path.parent
    with NamedTemporaryFile('w', dir=dirpath, delete=False, encoding='utf-8') as tf:
        json.dump(data, tf, ensure_ascii=False, indent=None)
        tf.flush()
        tempname = tf.name
    # atomic replace
    os.replace(tempname, path)


def log_event(session_id: str, event_type: str, payload: dict):
    """Append an event to in-memory logs and persist to logs/{session_id}.json as a JSON array.
    Event: { ts, type, payload }
    """
    ts = time.time()
    event = {"ts": ts, "type": event_type, "payload": payload}

    # Append to in-memory
    state = sessions_state.get(session_id)
    if state is not None:
        with state["lock"]:
            state_logs = state.setdefault("logs", [])
            state_logs.append(event)

    # Persist to file (read-modify-write) under global LOG_LOCK
    file_path = _log_file_path(session_id)
    with LOG_LOCK:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
            except Exception:
                # fallback to empty list on parse error
                existing = []
        else:
            existing = []
        existing.append(event)
        try:
            _atomic_write_json(file_path, existing)
        except Exception as e:
            # If persist fails, keep in-memory logs and print
            print(f"ERROR: failed to persist logs for session {session_id}: {e}")


def read_session_logs(session_id: str):
    """Read logs from JSON file and return list of events."""
    file_path = _log_file_path(session_id)
    if not file_path.exists():
        return []
    with LOG_LOCK:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    # fallback to in-memory if file unreadable
    state = sessions_state.get(session_id)
    if state is not None:
        with state['lock']:
            return list(state.get('logs', []))
    return []


def init_server_session(session_id):
    if session_id in sessions_state:
        return sessions_state[session_id]

    initial_message = "Book store xin chào! Tôi có thể giúp gì cho bạn?"
    state = {
        "pending_items": [],  # list of dicts: { message, future }
        "timer": None,
        "lock": threading.Lock(),
        "chat_history": [{"role": "model", "parts": [initial_message]}],
        "order_state": {
            "cart": [], "customer_name": None, "phone": None,
            "address": None, "confirming": False, "total_price": 0
        },
        "last_query_result": None,
        "processing": False,  # True when final LLM batch is running
        "logs": []  # in-memory event list (also persisted to file)
    }
    sessions_state[session_id] = state

    # Ensure log file exists and write initial session init event if empty
    file_path = _log_file_path(session_id)
    with LOG_LOCK:
        if not file_path.exists():
            try:
                _atomic_write_json(file_path, [])
            except Exception:
                pass
    log_event(session_id, "session_init", {"message": "session initialized"})
    return state


def _reset_order_state_struct():
    return {
        "cart": [], "customer_name": None, "phone": None,
        "address": None, "confirming": False, "total_price": 0
    }


def classify_and_sql_task(session_id, message, snapshot_chat_history):
    """Run classify_intent and (if needed) run quick DB handling (e.g., query_books) and return dict.
    Also logs the classify/sql result per-session.
    """
    try:
        intent = bot.classify_intent(message, snapshot_chat_history)
    except Exception as e:
        intent = None
        # Log classification error
        log_event(session_id, "classify_error", {"message": message, "error": str(e)})
    sql_result = None
    try:
        if intent == "query_books":
            # handle_query_books returns (final_answer, sql_result) but here we only want sql_result
            _, sql_result = bot.handle_query_books(message, snapshot_chat_history)
    except Exception as e:
        sql_result = {"error": str(e)}
        log_event(session_id, "sql_error", {"message": message, "error": str(e)})
    # Log classification result
    log_event(session_id, "classify_result", {"message": message, "intent": intent, "sql_result": sql_result})
    return {"message": message, "intent": intent, "sql_result": sql_result}


def _process_batch(session_id, batch_items):
    """batch_items: list of dicts {message,intent,sql_result}
    This runs in a background thread and calls final LLM handlers. Always appends the LLM response to chat_history.
    """
    state = sessions_state.get(session_id)
    if state is None:
        return

    with state["lock"]:
        state["processing"] = True

    # Log that final batch processing started
    log_event(session_id, "batch_start", {"batch_size": len(batch_items)})

    chat_history = state.get("chat_history", [])
    order_state = state.get("order_state", {})
    last_query_result = state.get("last_query_result", None)

    # Build final prompt (customize as needed)
    parts = []
    for it in batch_items:
        msg = it.get("message", "")
        intent = it.get("intent", "")
        sqlr = it.get("sql_result", None)
        p = f"User: {msg}\nIntent: {intent}"
        if sqlr is not None:
            p += f"\nSQL result: {sqlr}"
        parts.append(p)
    final_prompt = "\n\n---\n\n".join(parts).strip()

    final_answer = ""
    try:
        # Decide handler based on intents present
        intents = [it.get("intent") for it in batch_items if it.get("intent")]
        if any(i in ["order_book", "edit_order", "confirm_order", "reconsider_order"] for i in intents):
            final_answer = bot.handle_ordering(final_prompt, order_state, chat_history, last_query_result)
        elif any(i == "query_books" for i in intents):
            final_answer = bot.handle_chitchat(final_prompt)
        else:
            final_answer = bot.handle_chitchat(final_prompt)
    except Exception as e:
        final_answer = f"Xin lỗi, lỗi khi gọi model cuối: {e}"
        log_event(session_id, "llm_error", {"error": str(e), "prompt": final_prompt})

    concatenated_messages = "\n".join([it.get("message", "") for it in batch_items]).strip()

    # Append to chat_history (always print immediately when LLM returns)
    with state["lock"]:
        chat_history.append({"role": "user", "parts": [concatenated_messages]})
        chat_history.append({"role": "model", "parts": [final_answer]})
        # update states
        state["chat_history"] = chat_history
        state["order_state"] = order_state
        state["last_query_result"] = last_query_result
        state["processing"] = False

    # Log LLM response
    log_event(session_id, "llm_response", {"prompt": final_prompt, "response": final_answer, "batch_size": len(batch_items)})

    print(f"DEBUG: LLM batch processed for session {session_id}, batch size {len(batch_items)}")


def _start_final_processing_thread(session_id, batch_items):
    # Use LLM_POOL to schedule heavy calls (limits concurrency)
    LLM_POOL.submit(_process_batch, session_id, batch_items)


def _timer_callback(session_id):
    """When debounce fires:
     - snapshot pending_items (futures)
     - wait shortly for futures to complete (with timeout)
     - collect results and start final LLM processing in background
    """
    state = sessions_state.get(session_id)
    if state is None:
        return

    with state["lock"]:
        pending = state["pending_items"][:]
        state["pending_items"] = []
        state["timer"] = None

    # Log timer fire and how many pending items were snapshot
    log_event(session_id, "timer_fire", {"snapshot_count": len(pending)})

    if not pending:
        return

    completed_items = []
    # wait timeout per item (tune as needed)
    wait_timeout = max(1.0, DEBOUNCE_SECONDS - 1.0)
    for p in pending:
        future = p.get("future")
        if future is None:
            completed_items.append({"message": p.get("message"), "intent": None, "sql_result": None})
            continue
        try:
            res = future.result(timeout=wait_timeout)  # res = {message,intent,sql_result}
            completed_items.append(res)
        except concurrent.futures.TimeoutError:
            # include message without sql result but don't block
            completed_items.append({"message": p.get("message"), "intent": None, "sql_result": {"error": "classify/sql timeout"}})
            log_event(session_id, "classify_timeout", {"message": p.get("message")})
        except Exception as e:
            completed_items.append({"message": p.get("message"), "intent": None, "sql_result": {"error": str(e)}})
            log_event(session_id, "classify_exception", {"message": p.get("message"), "error": str(e)})

    # Start final LLM call in background
    _start_final_processing_thread(session_id, completed_items)

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]
    init_server_session(session_id)
    server_state = sessions_state.get(session_id, {})
    return render_template("index.html", chat_history=server_state.get("chat_history", []))

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if user_input is None:
        return jsonify({"error": "No message provided"}), 400

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]

    state = init_server_session(session_id)

    with state["lock"]:
        total_pending = len(state["pending_items"])
        if total_pending >= MAX_QUEUE_SIZE:
            log_event(session_id, "queue_rejected", {"message": user_input, "reason": "max_pending"})
            return jsonify({"error": "Bạn đã gửi tối đa 10 request liên tiếp. Vui lòng đợi kết quả."}), 429

        # Snapshot chat_history for classifier context
        snapshot_history = list(state["chat_history"])
        future = CLASSIFY_POOL.submit(classify_and_sql_task, session_id, user_input, snapshot_history)
        state["pending_items"].append({"message": user_input, "future": future})

        # Reset debounce timer
        if state["timer"] is not None:
            try:
                state["timer"].cancel()
            except Exception:
                pass
        timer = threading.Timer(DEBOUNCE_SECONDS, _timer_callback, args=(session_id,))
        timer.daemon = True
        state["timer"] = timer
        timer.start()

        queued_count = len(state["pending_items"])
        processing = state["processing"]

    # Log request queued
    log_event(session_id, "message_queued", {"message": user_input, "queued": queued_count, "processing": processing})

    # Return immediate acknowledgement
    return jsonify({
        "status": "queued",
        "queued": queued_count,
        "processing": processing,
        "message": f"Đã nhận yêu cầu. Hệ thống sẽ gom các yêu cầu trong {DEBOUNCE_SECONDS}s rồi xử lý batch."
    })

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
            "queue_length": len(state.get("pending_items", [])),
            "processing": state.get("processing", False)
        })

@app.route("/logs", methods=["GET"])
def logs():
    """Return session logs as JSON array (read from persisted file)."""
    if "session_id" not in session:
        return jsonify({"error": "No session"}), 400
    session_id = session["session_id"]
    events = read_session_logs(session_id)
    return jsonify({"logs": events})

if __name__ == "__main__":
    # Development server. In production use a WSGI server and shared backing store.
    app.run(debug=True)
"""