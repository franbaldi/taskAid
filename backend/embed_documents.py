# backend/embed_documents.py
import logging
import traceback
from pymongo import MongoClient, UpdateOne
from sentence_transformers import SentenceTransformer
from .config import MONGO_URI

model = SentenceTransformer("all-MiniLM-L6-v2")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

client = MongoClient(MONGO_URI)
db = client["barcelona_businesses"]
collection = db["businesses"]

def generate_document_embedding(doc, model):
    """
    Generate an embedding using only the 'reviews' field of a document.
    Cleans the reviews by ensuring all items are non-empty strings.
    
    Args:
        doc (dict): A MongoDB document.
        model (SentenceTransformer): The sentence transformer model used for encoding.
    
    Returns:
        list or None: The document embedding as a list of floats, or None if not possible.
    """
    reviews = doc.get("reviews")
    
    if not reviews:
        logging.warning(f"Document {doc.get('_id')} has no reviews.")
        return None

    # Ensure reviews is a list; if not, convert it to a list.
    if not isinstance(reviews, list):
        reviews = [reviews]

    # Clean reviews: ensure each review is a non-empty string.
    cleaned_reviews = [str(review).strip() for review in reviews if review is not None and str(review).strip()]
    if not cleaned_reviews:
        logging.warning(f"Document {doc.get('_id')} has no valid review strings.")
        return None

    combined_text = " ".join(cleaned_reviews)
    
    try:
        embedding = model.encode(combined_text)
        return embedding.tolist()
    except Exception as e:
        logging.error(f"Error generating embedding for document {doc.get('_id')}: {e}")
        traceback.print_exc()
        return None

def embed_documents():
    """
    Retrieves all documents from the collection, generates embeddings from the 'reviews' field,
    and updates each document with the new 'embeddings' field using bulk writes for efficiency.
    """
    # Initialize the model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    documents = collection.find({})
    bulk_updates = []
    processed_count = 0
    skipped_count = 0

    for doc in documents:
        embedding = generate_document_embedding(doc, model)
        if embedding is None:
            skipped_count += 1
            continue
        bulk_updates.append(
            UpdateOne({"_id": doc["_id"]}, {"$set": {"embeddings": embedding}})
        )
        processed_count += 1

        # Write in batches of 100 updates to optimize performance
        if len(bulk_updates) >= 100:
            result = collection.bulk_write(bulk_updates)
            logging.info(f"Bulk updated {result.modified_count} documents.")
            bulk_updates = []

    # Write any remaining updates
    if bulk_updates:
        result = collection.bulk_write(bulk_updates)
        logging.info(f"Bulk updated {result.modified_count} documents.")

    logging.info(f"Embedding complete: {processed_count} processed, {skipped_count} skipped.")

if __name__ == "__main__":
    try:
        embed_documents()
    except Exception as exc:
        logging.error("An unexpected error occurred in embed_documents.py:")
        traceback.print_exc()