'use client';

import { useCallback } from 'react';
import { ChatInterface } from '@/components/chat-interface';
import { pestKnowledgeRetrieval } from '@/ai/flows/pest-knowledge-retrieval';

export default function KnowledgePage() {

  // Memoize the callback functions to prevent unnecessary re-renders of the ChatInterface component.
  // This is a performance optimization that ensures the functions are not recreated on every render.
  const transformInput = useCallback((message: string) => {
    return {
      query: message,
    };
  }, []);

  const extractResponse = useCallback((result: any) => {
    return result.response;
  }, []);

  return (
    <div className="flex flex-col gap-8">
        <div>
            <h1 className="text-3xl font-bold">Knowledge Base</h1>
            <p className="text-muted-foreground">Ask our AI pest expert for information.</p>
        </div>
        <ChatInterface
            action={pestKnowledgeRetrieval}
            transformToActionInput={transformInput}
            extractResponse={extractResponse}
            greeting="I am your AI pest control expert. What would you like to know?"
            placeholder="e.g., 'How do I get rid of ants?'"
        />
    </div>
  );
}
