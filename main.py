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

def update_history(user_id, user_msg, bot_msg, context_data=None):
    history = get_history(user_id)
    history.append({"role": "user", "content": user_msg})

    full_bot_content = bot_msg

    if context_data:
        full_bot_content += f"\n\n[Dữ liệu tham khảo]: {json.dumps(context_data, ensure_ascii=False)}"
    history.append({"role": "assistant", "content": full_bot_content})
    #history.append({"role": "system", "content": context_data})
    if len(history) > 20:
        chat_histories[user_id] = history[-10:]

def resolve_confirm_action(intent, entities):
    confirm_status = entities.get('confirm')

    if confirm_status in ['yes', 'no', 'refine']:
        return confirm_status
    return 'UNKNOWN'

def handle_pending_confirmation(user_id, intent, entities, order_id):
    """
    xử lý khi đang ở 'confirming'
    """
    session = user_sessions[user_id]

    conn = database.get_connection()
    curr = conn.execute("SELECT status FROM Orders WHERE order_id = ?", (order_id,)) # chỉ là con trỏ, không lấy data ra
    row = curr.fetchone()
    conn.close()

    if not row:
        session['pending_order_id'] = None
        return ("Don hang khong ton tai!", False)

    db_status = row['status']
    
    action = resolve_confirm_action(intent, entities)
    print(f"🔍 Pending Action: {action} | Entity Confirm: {entities.get('confirm')}")

    if action == 'yes':
        if db_status == 'confirming':
            print('confirming')
            if database.finalize_to_pending(order_id):
                session['pending_order_id'] = None
                return (f"✅ Xác nhận thành công! Đơn hàng #{order_id} đã được chuyển đi.", True)
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
            return ("Đơn hàng này đã được xử lý xong rồi ạ.", True)
            
    elif action == 'no':
        if db_status == 'confirming':
            database.cancel_restock(order_id, reason='User cancel')
        session["pending_order_id"] = None # Reset trạng thái chờ
        return ("👌 Đã hủy yêu cầu. Bạn cần tìm sách nào khác không?", False)
    elif action == 'refine':
        if db_status == 'confirming':
            database.cancel_restock(order_id, reason='User refine')
        session['pending_order_id'] = None
        return ("Mình đã cập nhật đơn mới cho bạn.", False)
    
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

    #pending_oid = session['pending_order_id']

    history = get_history(user_id)

    #should_run_nlu = True

        
    nlu_result = nlu.analyze_input(user_input, history)

    intent = nlu_result.get("intent", "other")
    entities = nlu_result.get("entities", {})
    print(f"💡 [NLU]: {intent} | Entities: {json.dumps(entities, ensure_ascii=False)}")

    bot_response = ""
    pending_oid = session['pending_order_id']

    context_to_save = None

    if pending_oid:
        resp_text, is_finished = handle_pending_confirmation(user_id, intent, entities, pending_oid)

        if is_finished:
            print(f"🤖 Bot: {resp_text}")
            update_history(user_id, user_input, resp_text)
            return
        print(f"🤖 Bot (Refine Flow): {resp_text}")
#------------------
# PLACE ORDER
#-------------------------------------------
    if intent == "place_order":
        items = entities.get("book_keywords", [])
        cust_info = entities.get("customer_info", {})

        if not items:
            bot_response = "Bạn muốn đặt mua cuốn sách nào ạ?"
        else:
            found = None
            verified_items_count = 0

            for item in items:
                kw = item.get('book')
                qty = item.get('quantity', 1)
                candidates = database.search_book(kw)

                unique_candidates = []
                seen_ids = set()
                for c in candidates:
                    if c['book_id'] not in seen_ids:
                        unique_candidates.append(c)
                        seen_ids.add(c['book_id'])
                
                exact_match = None
                for c in unique_candidates:
                    if c['title'].lower().strip() == kw.lower().strip():
                        exact_match = c
                        break
                if exact_match:
                    unique_candidates = [exact_match]
                if len(unique_candidates) == 0:
                    bot_response = f"Rất tiếc, tiệm mình không có cuốn '{kw}' trong kho."
                    found = True
                    break
                elif len(unique_candidates) > 1:
                    found = True
                    list_txt = ""
                    for idx, b in enumerate(unique_candidates, 1):
                        status = "Còn hàng" if b['stock'] > 0 else "Hết hàng"
                        list_txt += f"{idx}. {b['title']} - Tác giả: {b['author']} - Giá: {b['price']:,.0f}đ - {status}\n"
                    bot_response = (
                        f"Mình tìm thấy nhiều cuốn sách liên quan đến '{kw}':\n{list_txt}"
                        f"Bạn vui lòng chọn lại tên sách chính xác để mình kiểm tra kho nhé!"
                    )
                    context_candidates= unique_candidates
                    break
                else:
                    verified_items_count += 1
            
            if found:
                #print(f"🤖 Bot: {bot_response}")
                pass
                if context_candidates:
                    data_str = database.format_books_for_history(context_candidates)
                    update_history(user_id, user_input, bot_response, context_data=data_str)
                else:
                    update_history(user_id, user_input, bot_response)
                    return

            else:
                missing = []
                if not cust_info.get('name'): missing.append("Tên")
                if not cust_info.get('phone'): missing.append("Số điện thoại")
                if not cust_info.get('address'): missing.append("Địa chỉ")

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
                    #handle_pending_confirmation(user_id, user_input, session['pending_order_id'])

#---------------------
# SEARCH / RECOMMEND BOOKS
#------------------------------------------------

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
        if author_kws:
            for aut in author_kws:
                all_found_books.extend(database.search_book(aut, limit=5))
        if cat_kws:
            for cat in cat_kws:
                all_found_books.extend(database.search_book(cat, limit=5))
        if not all_found_books:
            all_found_books = database.search_book(None, limit=5)  

        unique_books = []
        seen_ids = set()
        for b in all_found_books:
            if b['book_id'] not in seen_ids:
                unique_books.append(b)
                seen_ids.add(b['book_id'])
        bot_response = nlg.generate_response(user_input, history, unique_books, intent)
        if unique_books:
            context_to_save = database.format_books_for_history(unique_books)
#------------------
# CHECK ORDERS STATUS
#---------------------------------------------------
    elif intent == 'order_management':
        phone = entities.get('customer_info', {}).get('phone')

        if not phone:
            phone = session.get('last_phone')
        if not phone:
            bot_response = "Bạn cho mình xin số điện thoại để kiểm tra đơn hàng nhé."
        else:
            session['last_phone'] = phone
            data = database.get_order_by_phone(phone)
            if not data:
                bot_response = f"Không tìm thấy đơn hàng nào liên quan đến số điện thoại: {phone}."
            else:
                bot_response = nlg.generate_response(user_input, history, data, intent)
                context_to_save = database.format_orders_for_history(data)
    
    elif intent == 'general_support':
        bot_response = nlg.generate_response(user_input, history, None, intent)

    else:
        bot_response = config.OTHER_RESPONSE
    
    print(f"🤖 Bot: {bot_response}")

    update_history(user_id, user_input, bot_response, context_data=context_to_save)


if __name__ == "__main__":
    if not os.path.exists(config.DB_PATH):
        print("⚠️ Database chưa tồn tại. Chạy setup_database.py trước!")
        sys.exit(1)
    
    print("------------Tiệm sách của Nga nè------------")
    current_user = "user_demo_v3"

    while True:
        try:
            txt = input('\nUSER: ')
            if txt.lower() in ['exit', 'quit', 'q']: break

            if txt.startswith('admin update'):
                try:
                    parts = txt.split()
                    print(database.admin_update_status(parts[-2], parts[-1]))
                except:
                    print("error syntax.")
                continue
            run_bot(current_user, txt)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
