#!/usr/bin/env python3
"""
Test script for the Python NLP backend
"""

import requests
import json

def test_backend():
    """Test the Python NLP backend endpoints"""
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test context extraction
    test_query = "How to get rid of cockroaches in the kitchen?"
    
    try:
        response = requests.post(
            f"{base_url}/extract-context",
            json={"query": test_query},
            headers={"Content-Type": "application/json"}
        )
        print(f"\nContext extraction for '{test_query}':")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Context extraction failed: {e}")
    
    # Test keyword extraction
    try:
        response = requests.post(
            f"{base_url}/extract-keywords",
            json={"text": test_query},
            headers={"Content-Type": "application/json"}
        )
        print(f"\nKeyword extraction for '{test_query}':")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Keyword extraction failed: {e}")
    
    # Test knowledge base search
    try:
        response = requests.post(
            f"{base_url}/search-knowledge-base",
            json={"query": test_query, "top_k": 2},
            headers={"Content-Type": "application/json"}
        )
        print(f"\nKnowledge base search for '{test_query}' (top 2):")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Knowledge base search failed: {e}")

if __name__ == "__main__":
    test_backend()