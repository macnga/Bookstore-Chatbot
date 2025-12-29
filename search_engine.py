import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from google.genai import types
import config
import database
import os

client = None
book_vectors = None
book_ids = None
id_to_index_map = {}

def load_resource():
    global client, book_vectors, book_ids, id_to_index_map

    if not os.path.exists("book_embeddings.pkl"):
        print("❌ Embedding file not found. Please run build_embedding.py first.")
        return False
    try:
        client = genai.Client(api_key=config.GOOGLE_API_KEY)

        with open('book_embeddings.pkl', 'rb') as f:
            data = pickle.load(f)
            book_ids = data['ids']
            book_vectors = data['vectors']
        
        print("✅ Resources loaded successfully.")
        return True
    except Exception as e:
        print(f"❌ Error loading resources: {e}")
        return False


def search_semantic(query, limit=5, threshold=0.3):
    global client, book_vectors, book_ids

    if client is None or book_vectors is None or book_ids is None:
        print("❌ Resources not loaded. Call load_resource() first.")
        return []

    try:
        response = client.models.embed_content(
            model='text-embedding-004',
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )

        query_vector = np.array(response.embeddings[0].values).reshape(1, -1)
        book_matrix = np.array(book_vectors)

        similarities = cosine_similarity(query_vector, book_matrix)[0]

        results = []
        for idx in np.argsort(similarities)[-limit:][::-1]:
            if similarities[idx] >= threshold:
                book_id = book_ids[idx]
                book_info = database.get_book_by_id(book_id)
                if book_info:
                    results.append(book_info)

        return results
    except Exception as e:
        print(f"❌ Semantic Search Error: {e}")
        return []


def rerank_books(query, candidate_books, limit=5):
    global clinet, book_vectors, id_to_index_map
    if not candidate_books: return []

    if client is None: load_resource()

    try:
        subset_vectors = []
        valid_candidates = []
        for book in candidate_books:
            bid = book['book_id']
            for bid in id_to_index_map:
                idx = id_to_index_map[bid]
                subset_vectors.append(book_vectors[idx])
                valid_candidates.append(book)
        if not valid_candidates:
            return candidate_books[:limit]

        response = client.models.embed_content(
                model = 'text-embedding-004',
                contents = query,
                config = types.EmbedContentConfig(task_type='RETRIEVAL_QUERY')
        )
        query_vec = np.array(response.embeddings[0].values).reshape(1, -1)
        subset_vectors_np = np.array(subset_vectors)
        scores = cosine_similarity(query_vec, subset_vectors_np)[0]
        ranked_results = []
        for i, book in enumerate(valid_candidates):
            book['score'] = scores[i]
            ranked_results.append(book)
        ranked_results.sort(key=lambda x: x['score'], reverse=True)
        return ranked_results[:limit]
    except Exception as e:
        print(f"Rerank Error: {e}')
        return candidate_books[:limit]
        
