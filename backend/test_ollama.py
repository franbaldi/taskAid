import requests
import json

def test_ollama():
    print("Testing Ollama API connection...")
    
    try:
        # 1. Check if Ollama is running
        health = requests.get("http://localhost:11434/api/health", timeout=2)
        print(f"Health check status: {health.status_code}")
        
        # 2. List available models
        models = requests.get("http://localhost:11434/api/tags", timeout=2)
        print(f"Models endpoint status: {models.status_code}")
        
        if models.status_code == 200:
            models_data = models.json()
            print(f"Available models: {json.dumps(models_data, indent=2)}")
        
        # 3. Test a simple prompt
        test_prompt = "Say hello in one sentence."
        print(f"Testing simple prompt: '{test_prompt}'")
        
        # Try with the first available model, or default to llama2
        model_to_use = "llama2"
        if models.status_code == 200 and models.json().get("models") and len(models.json().get("models")) > 0:
            model_to_use = models.json().get("models")[0].get("name")
            
        print(f"Using model: {model_to_use}")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model_to_use, "prompt": test_prompt, "stream": False},
            timeout=10
        )
        
        print(f"Generate endpoint status: {response.status_code}")
        print(f"Raw response: {response.text[:200]}...")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except ValueError as e:
                print(f"Failed to parse response as JSON: {str(e)}")
    
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_ollama()