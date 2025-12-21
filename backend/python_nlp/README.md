# Python NLP Backend for Token Consumption Reduction

## Overview

This Python backend uses spaCy NLP and TF-IDF vectorization to reduce token consumption in AI conversations by extracting only relevant context from the knowledge base.

## Problem Solved

The original implementation loaded the entire knowledge base into each AI prompt, causing excessive token consumption. This backend:

1. Analyzes user queries to extract relevant keywords and entities
2. Uses semantic search to find the most relevant knowledge base documents
3. Sends only the relevant content to the AI, dramatically reducing token usage
4. Maintains accuracy by focusing on contextually relevant information

## Architecture

```
User Query → Python NLP Backend → Relevant KB Content → AI Model
```

## Features

- **spaCy NLP Processing**: Extracts entities, keywords, and performs linguistic analysis
- **TF-IDF Semantic Search**: Finds semantically similar documents efficiently
- **Context Extraction**: Identifies pests, products, locations, and other entities
- **Relevance Scoring**: Ranks documents by relevance to the query
- **Fallback Mechanism**: Falls back to full KB if backend is unavailable

## Endpoints

- `GET /health` - Health check
- `POST /extract-context` - Extract context and find relevant documents
- `POST /search-knowledge-base` - Search for relevant documents
- `POST /extract-keywords` - Extract keywords from text

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

3. Start the backend:
```bash
python main.py
```

## Usage with Frontend

The updated `pest-knowledge-retrieval-updated.ts` demonstrates integration with the main application:

```typescript
const response = await axios.post('http://localhost:5000/extract-context', { query });
const relevantContent = response.data.relevant_docs.map(doc => doc.content).join('\n');
```

## Docker Deployment

Build and run the backend using Docker:

```bash
docker build -t pest-control-nlp-backend .
docker run -p 5000:5000 pest-control-nlp-backend
```

## Benefits

- **Reduced Token Usage**: Only sends relevant content to AI models
- **Improved Performance**: Faster response times due to smaller prompts
- **Cost Efficiency**: Lower API costs from reduced token consumption
- **Scalability**: Can handle larger knowledge bases without performance impact
- **Maintainability**: Clean separation of NLP processing from AI logic