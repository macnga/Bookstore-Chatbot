# Xây dựng các hàm xử lý sau khi phân loại để lấy data đưa vào nlg - gen response
#version - 25.12.2025
# add data_str into history

import sqlite3
import datetime
import unidecode
from rapidfuzz import process, fuzz
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = 1") # Đảm bảo toàn vẹn tham chiếu
    return conn


#-------------------
# Using Fuzzy for search title, author, category instead of LIKE or = 
# -----------------------
def normalize_text(text):
    if not text: return ""

    text = text.lower()

    text = unidecode.unidecode(text)

    return text.strip()

#----------------------------------------
# SEARCH BOOK trong intent search_book, recommend_book
# Thực hiện search theo ký tự với title, author và category
#-----------------------------------------------------------

def search_book(user_keyword, limit=5, threshold = 60):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT book_id, title, author, category, price, stock FROM Books")
    all_books = [dict(row) for row in cursor.fetchall()]

    conn.close()

    if not user_keyword:
        return []
    
    query_norm = normalize_text(user_keyword)
    results = []
    for book in all_books:
        title = normalize_text(book['title'])
        author = normalize_text(book['author'])
        cat = normalize_text(book['category']) if book['category'] else ""

        score_title = fuzz.partial_ratio(query_norm, title)
        score_author = fuzz.partial_ratio(query_norm, author)
        score_cat = fuzz.partial_ratio(query_norm, cat)

        max_score = max(score_title, score_author, score_cat)

        if score_author > 90: max_score += 5

        if max_score >= threshold:
            results.append({
                    "score": max_score,
                    "data": book
                })
        
    results.sort(key=lambda x:x['score'], reverse=True)

    return [r['data'] for r in results[:limit]]

#-------------
# Đặt đơn
# Thực hiện kiểm tra kho, giữ đơn trong 2' đợi user xác nhận. Nếu 'có' trong 2' --> lên đơn; nếu 'không' --> hủy/sửa
# Nếu hold quá 2', xét điều kiện thứ 2 - session đợi 10'. Nếu 'có' khi session còn hạn --> lên đơn luôn nếu còn; 'không'/hết hạn phiên --> hủy đơn


def create_orders_transaction(items, customer_name, phone, address):
    """
    Thực hiện tạo đơn treo để chờ xác nhận (confirming)
    - vẫn trừ trong stock
    - Vẫn tạo đơn
    - Sẽ hủy nếu quá thời gian chờ xác nhận
    """
    conn = get_connection()
    cursor = conn.cursor()

    valid_items = []
    total_amount = 0

    try:
        for item in items:
            keyword = item['book']
            qty = item['quantity']
            matches = search_book(keyword, limit=1)

            if not matches:
                raise Exception(f"Not found books satisfied with '{keyword}")
            
            book = matches[0]
            if book['stock'] < qty:
                if book['stock'] == 0:
                    raise Exception(f"Xin lỗi, Sách '{book['title']}' đã hết hàng!")
                else:
                    raise Exception(f"Sách '{book['title']}' chỉ còn {book['stock']} cuốn.")
            
            valid_items.append({
                "book_id": book['book_id'],
                "title": book['title'],
                "price": book['price'],
                "quantity": qty
            })

            total_amount += book['price'] * qty
        

        cursor.execute("""
                INSERT INTO Orders (customer_name, phone, address, total_amount, status)
                VALUES (?, ?, ?, ?, 'confirming')
        """, (customer_name, phone, address, total_amount))

        new_order_id = cursor.lastrowid

        for v_item in valid_items:

            cursor.execute("""
                    INSERT INTO OrderDetails (order_id, book_id, quantity, price_at_purchase)
                    VALUES (?, ?, ?, ?)
            """, (new_order_id, v_item['book_id'], v_item['quantity'], v_item['price']))


            cursor.execute("UPDATE Books SET stock = stock - ? WHERE book_id = ?", (v_item['quantity'], v_item['book_id']))
        
        conn.commit()
        summary = "\n".join([f"- {i['title']} (x{i['quantity']})" for i in valid_items])
        return {
            "status": "success",
            "order_id": new_order_id,
            "summary": summary,
            "total": total_amount
        }

    except Exception as e:
        conn.rollback() # Hoàn tác nếu có lỗi
        return {"status": "fail", "msg": str(e)}
    finally:
        conn.close()

#-------------------------------------
# PLACE ORDER: Decrease stock and create a new order in DB
def finalize_to_pending(order_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                UPDATE Orders SET status = 'pending'
                WHERE order_id = ? AND status = 'confirming'
        """, (order_id,))


        success = cursor.rowcount() > 0
        
        conn.commit()
        return success
    
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()

def cancel_restock(order_id, reason='User Cancel'):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT status FROM Orders WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()

        if not order or order['status'] != 'confirming':
            return False
        
        cursor.execute("SELECT book_id, quantity FROM OrderDetails WHERE order_id = ?", (order_id,))
        details = cursor.fetchall()

        for item in details:
            cursor.execute("UPDATE Books SET stock = stock + ? WHERE book_id = ?", (item['quantity'], item['book_id']))

        cursor.execute("UPDATE Orders SET status = 'cancel' WHERE order_id = ?", (order_id,))

        conn.commit()
        print(f"🔄 SYSTEM: Đã hoàn {order['quantity']} cuốn cho đơn #{order_id}. Lý do: {reason}")
        return True
    except Exception as e:
        print(f"Error restoring stock: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def cleaning_timeout_order(timeout_min = 2):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                SELECT order_id FROM Orders
                WHERE status = 'confirming'
                       AND create_at < datetime('now', '-{timeout_minutes} minutes', 'localtime')
            """)
        
        timeouts = cursor.fetchall()
        conn.close()

        count = 0
        if timeouts:
            for row in timeouts:
                if cancel_restock(row['order_id'], reason='timeout'):
                    count += 1
        return count
    except Exception as e:
        print(f"Error when Cleaning Up: {e}")
        return 0

def purge_old_orders(days = 5):
    conn = get_connection()
    cursor = conn.cursor()

    count = 0
    try:
        cursor.execute("""
                SELECT order_id FROM Orders
                WHERE create_at < datetime('now'    , '-{days} days', 'localtime')
        """)
        rows = cursor.fetchall()

        if not rows:
            return 0

        ids_to_delete = [str(r['order_id']) for r in rows]
        ids_str = ",".join(ids_to_delete) # Ví dụ: "1,2,5"

        # 2. Xóa chi tiết đơn hàng trước (OrderDetails)
        cursor.execute(f"DELETE FROM OrderDetails WHERE order_id IN ({ids_str})")
        
        # 3. Xóa đơn hàng (Orders)
        cursor.execute(f"DELETE FROM Orders WHERE order_id IN ({ids_str})")
        
        count = cursor.rowcount
        conn.commit()
    except Exception as e:
        print(f"❌ Error purge_old_orders: {e}")
        conn.rollback()
    finally:
        conn.close()
    return count

def format_books_for_history(books):
    if not books: return None

    simplified_books = []
    for b in books:
        simplified_books.append({
            "book_id": b['book_id'],
            "title": b['title'],
            "author": b['author'],
            "price": b['price'],
            "category": b['category']
        })
    return json.dumps({"books": simplified_books}, ensure_ascii=False)

def format_orders_for_history(orders):
    if not orders: return None
    simplified_orders = []
    for o in orders:
        simplified_orders.append({
            "order_id": o['order_id'],
            "total_amount": o['total_amount'],
            "status": o['status'],
            "create_at": o['create_at'],
            "items_summary": o['items_summary']
        })
    return json.dumps({"orders": simplified_orders}, ensure_ascii=False)

def revive_order_transaction(order_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT book_id, quantity FROM OrderDetails WHERE order_id = ?", (order_id, ))
        details = cursor.fetchall()

        if not details:
            return {"status": "fail", "msg": "Khong tim thay don hang."}
    
        for item in details:
            cursor.execute("SELECT title, stock FROM Books WHERE book_id = ?", (item['book_id'], ))
            book = cursor.fetchone()

            if book['stock'] < item['quantity']:
                return {
                    "status": "fail",
                    "msg": f"Tiec qua, cuon {book['title']} vua het!"
                }
            
            cursor.execute("UPDATE Books SET stock = stock - ? WHERE book_id = ?", (item['quantity'], item['book_id']))

            conn.commit()
            return {"status": "success", "msg": "Đã đặt đơn thành công!"}
        
    except Exception as e:
        conn.rollback()
        return {"status": "fail", "msg": f'Lỗi hệ thống {e}'}
    

def get_order_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        O.order_id,
        O.total_amount,
        O.status,
        O.create_at,
        GROUP_CONCAT(B.title || ' (x' || OD.quantity || ')', ', ') as items_summary
    FROM Orders O
    JOIN OrderDetails OD ON O.order_id = OD.order_id
    JOIN Books B ON OD.book_id = B.book_id
    WHERE O.phone = ? AND O.status != 'cancel' AND O.status != 'confirming'
    GROUP BY O.order_id
    ORDER BY O.create_at DESC
    LIMIT 5
    """
    cursor.execute(query, (phone,))
    
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def admin_update_status(order_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()

    valid_status = ["confirming", "pending", "shipping", "received", "cancel"]
    if new_status not in valid_status:
        return f"Status not competibale!"

    cursor.execute("UPDATE Orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    
    if cursor.rowcount == 0:
        return f"Order #{order_id} not found!"
    
    conn.commit()
    conn.close()

    return f"Updated order {order_id} into status - {new_status}!"

    
