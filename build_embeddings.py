import sqlite3
import pickle
import numpy as np
from google import genai
from google.genai import types
import time
import config


client = genai.Client(api_key=config.GOOGLE_API_KEY)

def build_index():
    print(f"Connecting to database at {config.DB_PATH}...")
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT book_id, title, content FROM Books")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No books found in the database.")
        return
    
    book_ids = []
    vectors = []

    batch_size = 10

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        texts_to_embed = []
        current_ids = []

        for r in batch:
            book_id, title, content = r
            text = f"{title}. Nội dung: {content}"
            texts_to_embed.append(text)
            current_ids.append(book_id)
        try:
            response = client.models.embed_content(
                model='text-embedding-004',
                contents = texts_to_embed,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )

            for emb in response.embeddings:
                vectors.append(emb.values)
            book_ids.extend(current_ids)
            print(f"Processed batch {i//batch_size + 1} / {(len(rows)-1)//batch_size + 1}")

            time.sleep(1)
        except Exception as e:
            print(f"❌ Embedding Error: {e}")
    with open("book_embeddings.pkl", "wb") as f:
        pickle.dump({'ids': book_ids, 'vectors': vectors}, f)
    print("Embeddings saved to book_embeddings.pkl")

if __name__ == "__main__":
    build_index()
