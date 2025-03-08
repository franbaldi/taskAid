import numpy as np
import requests
from pymongo import MongoClient, ASCENDING
from sentence_transformers import SentenceTransformer
from .config import MONGO_URI, OLLAMA_URL

# Lazy-loaded components
_model = None
_client = None
_collection = None

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
    collection = get_collection()
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

def query_llm(context: str, query: str):
    """Generate final response using OLLama"""
    prompt = f"""Context about service companies:
{context}

User query: {query}

Generate a helpful response using the context. Include company names, 
contact info, and relevant reviews. Be concise and business-like."""
    
    try:
        # List available models first
        models_response = requests.get("http://localhost:11434/api/tags")
        if models_response.status_code != 200:
            print(f"Failed to get models list: {models_response.status_code}")
            return "Couldn't retrieve available models from Ollama."
            
        models_data = models_response.json()
        print(f"Available models: {models_data}")
        
        # Check if any models are available
        available_models = []
        if "models" in models_data and models_data["models"]:
            available_models = [model["name"] for model in models_data["models"]]
            print(f"Found models: {available_models}")
        
        # Choose a model to use
        model_to_use = "llama2"
        if available_models and model_to_use not in available_models:
            # Use the first available model if llama2 isn't available
            model_to_use = available_models[0]
            print(f"Using alternative model: {model_to_use}")
        
        # Make the generation request
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_to_use,
                "prompt": prompt,
                "stream": False
            },
            timeout=30  # Longer timeout for model loading
        )
        
        if response.status_code != 200:
            print(f"Error from Ollama API: {response.status_code} - {response.text}")
            return f"Ollama returned an error: {response.status_code}"
        
        # Parse the response
        try:
            response_data = response.json()
            print(f"Response keys: {response_data.keys()}")
            
            if "response" in response_data:
                return response_data["response"]
            else:
                return f"Received response but couldn't find expected 'response' field. Available keys: {list(response_data.keys())}"
                
        except ValueError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {response.text[:200]}...")
            return "Received invalid response from Ollama."
            
    except Exception as e:
        print(f"Error in query_llm: {str(e)}")
        return f"Sorry, I couldn't process that request. Error: {str(e)}"

def retrieve_top_matches(query_embedding: list, top_k: int = 3):
    """RAG Pipeline using Atlas Vector Search"""
    create_vector_index()  # Ensure index exists before query
    collection = get_collection()
    
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

# Add the process_query function here
def process_query(query: str):
    """Simple processing pipeline without LLM dependency"""
    try:
        # 1. Embed the user's query
        model = get_model()
        query_embedding = model.encode(query).tolist()
        
        # 2. Perform vector search
        top_docs = retrieve_top_matches(query_embedding, top_k=3)
        
        if not top_docs:
            return "No matching services found. Please try different keywords."
        
        # 3. Format a simple response
        response = "Here are some businesses that match your query:\n\n"
        
        for i, doc in enumerate(top_docs):
            response += f"{i+1}. {doc.get('name', 'Unknown business')}\n"
            
            if 'address' in doc and doc['address']:
                response += f"   Location: {doc['address']}\n"
                
            if 'phone' in doc and doc['phone']:
                response += f"   Contact: {doc['phone']}\n"
            
            # Add a top review if available
            if 'reviews' in doc and doc['reviews'] and len(doc['reviews']) > 0:
                top_review = doc['reviews'][0]
                # Truncate long reviews
                if len(top_review) > 100:
                    top_review = top_review[:97] + "..."
                response += f"   Review: \"{top_review}\"\n"
            
            response += "\n"
        
        response += "How can I help you further?"
        return response
            
    except Exception as e:
        import logging
        logging.error(f"Error in process_query: {str(e)}", exc_info=True)
        return f"I encountered an issue while searching for businesses. Please try again with different keywords."