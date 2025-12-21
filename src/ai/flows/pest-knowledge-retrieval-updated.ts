// src/ai/flows/pest-knowledge-retrieval-updated.ts
'use server';

/**
 * @fileOverview A pest knowledge retrieval AI agent that uses Python NLP backend
 * to reduce token consumption by extracting only relevant context from the knowledge base.
 *
 * - pestKnowledgeRetrieval - A function that handles the pest knowledge retrieval process.
 * - PestKnowledgeRetrievalInput - The input type for the pestKnowledgeRetrieval function.
 * - PestKnowledgeRetrievalOutput - The return type for the pestKnowledgeRetrieval function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';
import {promises as fs} from 'fs';
import * as path from 'path';
import axios from 'axios';

const PestKnowledgeRetrievalInputSchema = z.object({
  query: z.string().describe('The pest-related question or query from the user.'),
});

export type PestKnowledgeRetrievalInput = z.infer<typeof PestKnowledgeRetrievalInputSchema>;

const PestKnowledgeRetrievalOutputSchema = z.object({
  response: z.string().describe('The chatbot response incorporating knowledge from the provided markdown files.'),
});

export type PestKnowledgeRetrievalOutput = z.infer<typeof PestKnowledgeRetrievalOutputSchema>;

interface RelevantDocument {
  filename: string;
  title: string;
  path: string;
  similarity_score: number;
  content: string;
}

interface ContextExtractionResponse {
  entities: {
    pests: string[];
    products: string[];
    locations: string[];
    symptoms: string[];
    other_entities: string[];
  };
  keywords: string[];
  original_query: string;
  relevant_docs: RelevantDocument[];
}

async function getRelevantKnowledgeBaseContent(query: string): Promise<string> {
  try {
    // Call the Python NLP backend to extract relevant content
    const response = await axios.post<ContextExtractionResponse>(
      'http://localhost:5000/extract-context',
      { query },
      { timeout: 10000 } // 10 second timeout
    );

    const { relevant_docs } = response.data;
    
    if (!relevant_docs || relevant_docs.length === 0) {
      return "لا توجد معلومات متاحة في قاعدة المعرفة حول هذا الموضوع.";
    }

    // Combine the content of relevant documents
    let content = '';
    for (const doc of relevant_docs) {
      content += `\n\n--- FILE: ${doc.filename} (${doc.title}) - Relevance Score: ${doc.similarity_score.toFixed(2)} ---\n\n`;
      content += doc.content;
    }

    return content;
  } catch (error) {
    console.error('Error calling Python NLP backend:', error);
    
    // Fallback: load all knowledge base content if Python backend is unavailable
    return await getFullKnowledgeBaseContent();
  }
}

async function getFullKnowledgeBaseContent(): Promise<string> {
  console.warn('Falling back to full knowledge base loading');
  const kbPath = path.join(process.cwd(), 'src', 'kb');
  const files = await fs.readdir(kbPath);
  let content = '';
  for (const file of files) {
    if (file.endsWith('.md')) {
      const filePath = path.join(kbPath, file);
      const fileContent = await fs.readFile(filePath, 'utf-8');
      content += `\n\n--- FILE: ${file} ---\n\n${fileContent}`;
    }
  }
  return content;
}

export async function pestKnowledgeRetrieval(input: PestKnowledgeRetrievalInput): Promise<PestKnowledgeRetrievalOutput> {
  return pestKnowledgeRetrievalFlow(input);
}

const pestKnowledgeRetrievalPrompt = ai.definePrompt({
  name: 'pestKnowledgeRetrievalPrompt',
  input: {
    schema: z.object({
      query: z.string(),
      knowledgeBase: z.string(),
    }),
  },
  output: {schema: PestKnowledgeRetrievalOutputSchema},
  prompt: `You are a pest control expert assistant. Your primary source of information is the knowledge base provided below.

If the answer is not found in the knowledge base, you MUST state that you do not have the information.
The user is asking a question in Arabic, so you MUST respond in Arabic.

Knowledge Base (with relevance scores):
{{{knowledgeBase}}}

---

User Query: {{{query}}}
`,
});

const pestKnowledgeRetrievalFlow = ai.defineFlow(
  {
    name: 'pestKnowledgeRetrievalFlow',
    inputSchema: PestKnowledgeRetrievalInputSchema,
    outputSchema: PestKnowledgeRetrievalOutputSchema,
  },
  async input => {
    const knowledgeBase = await getRelevantKnowledgeBaseContent(input.query);
    const {output} = await pestKnowledgeRetrievalPrompt({ ...input, knowledgeBase });
    return output!;
  }
);