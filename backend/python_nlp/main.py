#!/usr/bin/env python3
"""
Python Backend with spaCy NLP for Context Extraction and Relevance Matching
to reduce token consumption in AI conversations
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import spacy
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import markdown
import re


class KnowledgeBaseProcessor:
    """Process knowledge base documents and extract relevant content"""
    
    def __init__(self, kb_directory: str = "/workspace/src/kb"):
        self.kb_directory = Path(kb_directory)
        self.documents = {}
        self.processed_docs = []
        self.doc_metadata = []
        self.vectorizer = None
        self.tfidf_matrix = None
        
        # Load spaCy English model (you might want to install 'en_core_web_sm')
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model 'en_core_web_sm' not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        self._load_knowledge_base()
        self._prepare_search_index()
    
    def _load_knowledge_base(self):
        """Load all markdown files from the knowledge base directory"""
        md_files = list(self.kb_directory.glob("*.md"))
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Convert markdown to plain text for processing
                html_content = markdown.markdown(content)
                # Remove HTML tags to get plain text
                plain_text = re.sub('<[^<]+?>', '', html_content)
                
                self.documents[file_path.name] = {
                    'title': file_path.stem,
                    'content': plain_text,
                    'full_content': content,
                    'path': str(file_path)
                }
                
                # Add document to processed docs list
                self.processed_docs.append(plain_text)
                self.doc_metadata.append({
                    'filename': file_path.name,
                    'title': file_path.stem,
                    'path': str(file_path)
                })
                
            except Exception as e:
                logging.error(f"Error loading document {file_path}: {e}")
    
    def _prepare_search_index(self):
        """Prepare TF-IDF index for similarity search"""
        if not self.processed_docs:
            logging.warning("No documents loaded for indexing")
            return
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=10000
        )
        
        # Fit the vectorizer on all documents
        self.tfidf_matrix = self.vectorizer.fit_transform(self.processed_docs)
        logging.info(f"Indexed {len(self.processed_docs)} documents")
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from input text using spaCy"""
        doc = self.nlp(text.lower())
        
        # Extract named entities and important tokens
        keywords = []
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "PRODUCT", "GPE", "NORP"]:
                keywords.append(ent.text)
        
        # Important tokens (nouns, adjectives, verbs)
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_)
        
        # Remove duplicates while preserving order
        unique_keywords = []
        for kw in keywords:
            if kw not in unique_keywords:
                unique_keywords.append(kw)
        
        return unique_keywords
    
    def find_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find the most relevant documents for a given query"""
        if not self.vectorizer or self.tfidf_matrix is None:
            return []
        
        # Vectorize the query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top-k most similar documents
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        relevant_docs = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Only include documents with reasonable similarity
                doc_info = self.doc_metadata[idx].copy()
                doc_info['similarity_score'] = float(similarities[idx])
                doc_info['content'] = self.processed_docs[idx][:1000] + "..." if len(self.processed_docs[idx]) > 1000 else self.processed_docs[idx]
                relevant_docs.append(doc_info)
        
        return relevant_docs
    
    def extract_context_from_query(self, query: str) -> Dict:
        """Extract context information from user query"""
        doc = self.nlp(query)
        
        # Extract entities related to pests/products
        entities = {
            'pests': [],
            'products': [],
            'locations': [],
            'symptoms': [],
            'other_entities': []
        }
        
        for ent in doc.ents:
            ent_lower = ent.text.lower()
            
            # Classify entities based on keywords
            if any(pest in ent_lower for pest in ['bug', 'cockroach', 'ant', 'termite', 'rodent', 'rat', 'mouse', 'pest']):
                entities['pests'].append(ent.text)
            elif any(product in ent_lower for product in ['product', 'solution', 'treatment', 'spray', 'trap', 'poison']):
                entities['products'].append(ent.text)
            elif ent.label_ == 'GPE':  # Geopolitical entity
                entities['locations'].append(ent.text)
            else:
                entities['other_entities'].append(ent.text)
        
        # Extract keywords for semantic search
        keywords = self.extract_keywords(query)
        
        return {
            'entities': entities,
            'keywords': keywords,
            'original_query': query,
            'relevant_docs': self.find_relevant_documents(query)
        }


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global processor instance
processor = KnowledgeBaseProcessor()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Python NLP Backend'})


@app.route('/extract-context', methods=['POST'])
def extract_context():
    """Extract context from user query"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        context = processor.extract_context_from_query(query)
        return jsonify(context)
    
    except Exception as e:
        logging.error(f"Error in extract_context: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/search-knowledge-base', methods=['POST'])
def search_knowledge_base():
    """Search knowledge base for relevant documents"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 3)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        relevant_docs = processor.find_relevant_documents(query, top_k)
        return jsonify({'relevant_documents': relevant_docs})
    
    except Exception as e:
        logging.error(f"Error in search_knowledge_base: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/extract-keywords', methods=['POST'])
def extract_keywords():
    """Extract keywords from text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        keywords = processor.extract_keywords(text)
        return jsonify({'keywords': keywords})
    
    except Exception as e:
        logging.error(f"Error in extract_keywords: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)