import numpy as np
import requests
from pymongo import MongoClient, ASCENDING
from sentence_transformers import SentenceTransformer
from .config import MONGO_URI, OLLAMA_URL

# Lazy-loaded components
_model = None
_client = None
_collection = None

# Initialize MongoDB client and collection globally
client = MongoClient(MONGO_URI)
db = client["barcelona_businesses"]
collection = ["businesses"]  # Define the collection globally so it's accessible to all functions

def get_mongo_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
        
        # Ensure database and collection exist
        db = _client.get_database("barcelona_businesses")
        if "businesses" not in db.list_collection_names():
            db.create_collection("businesses")
    return _client

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_collection():
    global _collection
    if _collection is None:
        client = get_mongo_client()
        db = client["barcelona_businesses"]
        _collection = db["businesses"]
    return _collection

def create_vector_index():
    """Create vector index only if missing"""
    index_name = "vector_search_index"
    
    try:
        # Check for existing SEARCH indexes
        existing_search_indexes = list(collection.list_search_indexes(name=index_name))
        
        if not existing_search_indexes:
            index_definition = {
                "name": index_name,
                "definition": {
                    "mappings": {
                        "dynamic": True,
                        "fields": {
                            "embeddings": {
                                "type": "knnVector",
                                "dimensions": 384,
                                "similarity": "cosine"
                            }
                        }
                    }
                }
            }
            collection.create_search_index(index_definition)
            print(f"Created vector index '{index_name}'")
        else:
            print(f"Index '{index_name}' already exists")
            
    except Exception as e:
        print(f"Index check error: {str(e)}")

def retrieve_top_matches(query: str, top_k: int = 3):
    """RAG Pipeline using Atlas Vector Search"""
    create_vector_index()  # Ensure index exists before query
    model = get_model()
    collection = get_collection()
    
    query_embedding = model.encode(query).tolist()
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_search_index",
                "path": "embeddings",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": top_k,
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "address": 1,
                "phone": 1,
                "reviews": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    return list(collection.aggregate(pipeline))

def format_results(docs):
    """Format RAG results for LLM context"""
    return "\n\n".join(
        f"Company: {doc['name']}\n"
        f"Address: {doc['address']}\n"
        f"Phone: {doc['phone']}\n"
        f"Reviews: {' | '.join(doc['reviews'][:3])}"
        for doc in docs
    )

def query_llm(context: str, query: str):
    """Generate final response using OLLama"""
    prompt = f"""Context about service companies:
{context}

User query: {query}

Generate a helpful response using the context. Include company names, 
contact info, and relevant reviews. Be concise and business-like."""
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}",
            json={"model": "llama3.2", "prompt": prompt, "stream": False}
        )
        return response.json()["text"]
    except Exception as e:
        return f"Sorry, I couldn't process that request. Error: {str(e)}"

def process_query(query: str):
    """End-to-end processing pipeline"""
    # 1. Retrieve relevant documents
    top_docs = retrieve_top_matches(query)
    
    if not top_docs:
        return "No matching services found. Please try different keywords."
    
    # 2. Format context for LLM
    context = format_results(top_docs)
    
    # 3. Generate final response
    return query_llm(context, query)
