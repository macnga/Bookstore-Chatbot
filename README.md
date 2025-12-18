# Bookstore-Chatbot
A Chatbot of Nga's BookStore. Using the SQL database to answer question/request from customers.
Database includes 3 tables Books, Orders and OrderDetails
- Books: book_id, title, author, price, stock, category
- Orders: order_id, customer_name, phone, address, total_amount, status, create_at
- OrderDetails: detail_id, order_id, book_id, quantity, price_at_purchase


INPUT: NL from users

CHATBOT:
- Query from SQL database
- Add new order

# PIPELINE:
1. Intent Classify:
  Classify User's query into 1 of 6 intents:
  - 'search_book'
  - 'recommend_book'
  - 'place_order'
  - 'order_management'
  - 'general_support'
  - 'other'
2. Named Entity Extraction
FFrom User's query, extracting the following info:
- book_kws (list[object]):
  * book (string)
  * quantity (string)
- author_kws (list[str])
- category_kws (list[str])
- filters (object) (for price)
  * min_price (number/null)
  * max_price (number/null)
  * sort_by (string/null): "best_selling" | "newest" | "price_asc" | "price_desc"
- customer_info (object):
  * name (str)
  * phone (str)
  * address (str)
3. SQL Schema
4. Generate response
