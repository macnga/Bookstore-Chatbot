# Version 19.12.2025
# Thực hiện luồng ChatBot

import nlg
import nlu
import database
import time
import sys
import config
import json
import os


SESSION_TIMEOUT = 600
ORDER_TIMEOUT = 120
user_sessions = {}

chat_histories = {}

def get_create_session(user_id):
    now = time.time()

    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "pending_order_id": None,
            "last_active": now
        }

        if user_id not in chat_histories:
            chat_histories[user_id] = []
    
    user_sessions[user_id]['last_active'] = now
    return user_sessions[user_id]

def cleanup_inactive_session():
    now = time.time()

    expired_users = [
        uid for uid, sess in user_sessions.items()
        if now - sess['last_active'] > SESSION_TIMEOUT
    ]
    for uid in expired_users:
        print(f"🧹 Session: Xóa phiên của user '{uid}' do quá 10 phút không hoạt động.")
        del user_sessions[uid]
        if uid in chat_histories:
            del chat_histories[uid]
        


def get_history(user_id):
    return chat_histories[user_id]

def update_history(user_id, user_msg, bot_msg):
    history = get_history(user_id)
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_msg})
    if len(history) > 20:
        chat_histories[user_id] = history[-10:]



def handle_pending_confirmation(user_id, user_input, order_id):
    """
    xử lý khi đang ở 'confirming'
    """
    session = user_sessions[user_id]

    conn = database.get_connection()
    curr = conn.execute("SELECT status FROM Orders WHERE order_id = ?", (order_id,))
    conn.close()

    if not curr:
        session['pending_order_id'] = None
        return ("Don hang khong ton tai!", False)
    
    db_status = curr['status']

    
    txt = user_input.lower()
    is_agreed = any(w in txt for w in ["có", "ok", "chốt", "đồng ý", "mua", "yes", "đúng"])
    is_cancelled = any(w in txt for w in ["không", "hủy", "sai", "no", "khoan", "thôi"])
    if is_agreed:
        if db_status == 'confirming':
            if database.finalize_to_pending(order_id):
                session['pending_order_id'] = None
                return (f"✅ Xác nhận thành công! Đơn hàng #{order_id} đã được chuyển đi.", False)
            else:
                #session["pending_order_id"] = None
                return ("Có lỗi xảy ra.", False)
        if db_status == 'cancel':
            revive_result = database.revive_order_transaction(order_id)

            if revive_result['status'] == 'success':
                session['pending_order_id'] = None
                return (f"Van con hang! {revive_result['msg']} (ma #{order_id}).", False)
            else:
                # Hết hàng thật rồi -> Báo lỗi từ msg của DB
                session["pending_order_id"] = None
                return (f"😞 {revive_result['msg']} Bạn vui lòng chọn sách khác nhé.", False)
        else:
            session["pending_order_id"] = None
            return ("Đơn hàng này đã được xử lý xong rồi ạ.", False)
            
    elif is_cancelled:
        if db_status == 'confirming':
            database.cancel_restock(order_id, reason='User cancel')
        session["pending_order_id"] = None # Reset trạng thái chờ
        return ("👌 Đã hủy yêu cầu. Bạn cần tìm sách nào khác không?", False)
    else:
        extra_msg = ""
        if db_status == 'cancel':
            extra_msg = "\n (Đơn hàng đã quá thời gian giữ chỗ, nhưng nếu bạn chốt mình sẽ kiểm tra kho lại ngay)."
        return (f"Bạn vui lòng xác nhận 'Có' hoặc 'Không' để mình xử lý nhé.{extra_msg}", False)


def run_bot(user_id, user_input):
    bot_response = ""

    database.cleaning_timeout_order(timeout_min=2)
    cleanup_inactive_session()

    session = get_create_session(user_id)

    pending_oid = session['pending_order_id']

    should_run_nlu = True

    if pending_oid:
        resp_text, confirm_flag = handle_pending_confirmation(user_id, user_input, pending_oid)

        if not confirm_flag:
            print(f"🤖 Bot: {resp_text}")
            update_history(user_id, user_input, resp_text)
            return # Dừng, đợi user nhập câu tiếp theo
    if should_run_nlu:
        history = get_history(user_id)
        nlu_result = nlu.analyze_input(user_input, history)

        intent = nlu_result.get("intent", "other")
        entities = nlu_result.get("entities", {})
        print(f"💡 [NLU]: {intent} | Entities: {json.dumps(entities, ensure_ascii=False)}")
#------------------
# PLACE ORDER
#-------------------------------------------
        if intent == "place_order":
            items = entities.get("book_keywords", [])
            cust_info = entities.get("customer_info", {})

            if not items:
                bot_response = "Bạn muốn đặt mua cuốn sách nào ạ?"
            else:
                missing = []
                if not cust_info.get('name'): missing.append("Name")
                if not cust_info.get('phone'): missing.append("Phone Number")
                if not cust_info.get('address'): missing.append("Address")

                if missing:
                    book_txt = ", ".join([i.get('book', "Sach") for i in items])
                    bot_response = f"Để lên đơn cho: **{book_txt}**, bạn vui lòng cung cấp thêm: **{', '.join(missing)}** nhé."
                else:
                    result = database.create_orders_transaction(
                        items=items,
                        customer_name=cust_info.get('name'),
                        phone=cust_info.get('phone'),
                        address=cust_info.get('address')
                    )

                    if result['status'] == 'success':
                        session['pending_order_id'] = result['order_id']
                        bot_response = (
                            f"✅ Đã giữ hàng thành công!\n"
                            f"{result['summary']}\n"
                            f"💰 Tổng tiền: {result['total']:,.0f}đ\n"
                            f"📍 Giao tới: {cust_info['address']}\n"
                            f"👉 Bạn có chốt đơn không? (Có/Không)"
                        )

                    else:
                        bot_response = f"Rat tiec: {result['msg']}"


        elif intent in ['search_book', 'recommend_book']:
            raw_items = entities.get('book_keywords', [])
            author_kws = entities.get('author_keywords', [])
            cat_kws = entities.get('category_keywords', [])

            
            all_found_books = []
        #------------------TITLE OF BOOKS-------------------
            if raw_items:
                for item in raw_items:
                    kw = item.get('book')
                    if kw:
                        results = database.search_book(kw, limit=5)
                        all_found_books.extend(results)

        #---------------------AUTHOR OF BOOKS--------------------
            elif author_kws:
                for aut in author_kws:
                    all_found_books.extend(database.search_book(aut, limit=5))
            elif cat_kws:
                for cat in cat_kws:
                    all_found_books.extend(database.search_book(cat, limit=5))
            else:
                all_found_books = database.search_book(None, limit=5)  

            unique_books = []
            seen_ids = set()
            for b in all_found_books:
                if b['book_id'] not in seen_ids:
                    unique_books.append(b)
                    seen_ids.add(b['book_id'])
            bot_response = nlg.generate_response(user_input, unique_books, intent)

        elif intent == 'order_management':
            phone = entities.get('customer_info', {}).get('phone')

            if not phone:
                bot_response = "Bạn cho mình xin số điện thoại để kiểm tra đơn hàng nhé."
            else:
                orders = database.get_order_by_phone(phone)
                bot_response = nlg.generate_response(user_input, orders, intent)
        
        elif intent == 'general_support':
            bot_response = nlg.generate_response(user_input, None, intent)
        
        else:
            bot_response = config.OTHER_RESPONSE
        
        print(f"🤖 Bot: {bot_response}")
        update_history(user_id, user_input, bot_response)


if __name__ == "__main__":
    if not os.path.exists(config.DB_PATH):
        print("⚠️ Database chưa tồn tại. Chạy setup_database.py trước!")
        sys.exit(1)
    
    print("------------Tiệm sách của Nga nè------------")
    current_user = "user_demo_v2"

    while True:
        try:
            txt = input('\nUSER: ')
            if txt.lower() in ['exit', 'quit', 'q']: break

            if txt.startswith('admin update'):
                try:
                    parts = txt.split()
                    print(database.admin_update_status(parts[2], parts[3]))
                except:
                    print("error syntax.")
                continue
            run_bot(current_user, txt)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
