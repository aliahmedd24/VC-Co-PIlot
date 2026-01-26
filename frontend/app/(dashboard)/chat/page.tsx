"use client";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, User, Bot } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';

interface ChatMessage {
    role: string;
    content: string;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Create or get a chat session
    const getOrCreateSession = async (): Promise<string> => {
        if (sessionId) return sessionId;

        try {
            // Try to get existing sessions first
            const listResponse = await api.get('/chat/sessions?workspace_id=default');
            const sessions = listResponse.data.sessions || [];

            if (sessions.length > 0) {
                // Use the most recent session
                const existingSession = sessions[0];
                setSessionId(existingSession.id);
                return existingSession.id;
            }

            // Create new session
            const createResponse = await api.post('/chat/sessions?workspace_id=default', {
                title: 'New Conversation'
            });
            const newSessionId = createResponse.data.id;
            setSessionId(newSessionId);
            return newSessionId;
        } catch (err) {
            console.error('Failed to get/create session:', err);
            throw err;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg: ChatMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            // Get or create a session
            const currentSessionId = await getOrCreateSession();

            // Send message to the session
            const response = await api.post(`/chat/sessions/${currentSessionId}/messages`, {
                content: userMsg.content
            });

            // The response contains both user_message and assistant_message
            const assistantContent = response.data.assistant_message?.content || 'No response received';
            const botMsg: ChatMessage = { role: 'assistant', content: assistantContent };
            setMessages(prev => [...prev, botMsg]);
        } catch (err: any) {
            console.error('Chat error:', err);
            const errorMessage = err.response?.data?.detail || 'Error sending message. Please try again.';
            setError(errorMessage);
            setMessages(prev => [...prev, { role: 'system', content: errorMessage }]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    return (
        <div className="flex flex-col h-full max-h-[calc(100vh-2rem)] p-4">
            <Card className="flex-1 flex flex-col overflow-hidden bg-white shadow-sm">
                <ScrollArea className="flex-1 p-4">
                    <div className="space-y-4 max-w-3xl mx-auto">
                        {messages.length === 0 && (
                            <div className="text-center text-slate-400 mt-20">
                                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Start a conversation with your VC Co-Pilot</p>
                            </div>
                        )}
                        {messages.map((m, i) => (
                            <div
                                key={i}
                                className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'
                                    }`}
                            >
                                {m.role !== 'user' && (
                                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200">
                                        <Bot className="h-5 w-5 text-blue-600" />
                                    </div>
                                )}
                                <div
                                    className={`rounded-lg px-4 py-2 max-w-[80%] ${m.role === 'user'
                                            ? 'bg-blue-600 text-white'
                                            : m.role === 'system'
                                                ? 'bg-red-50 text-red-600 border border-red-200'
                                                : 'bg-slate-100 text-slate-800'
                                        }`}
                                >
                                    {m.content}
                                </div>
                                {m.role === 'user' && (
                                    <div className="h-8 w-8 rounded-full bg-slate-900 flex items-center justify-center">
                                        <User className="h-5 w-5 text-white" />
                                    </div>
                                )}
                            </div>
                        ))}
                        <div ref={scrollRef} />
                    </div>
                </ScrollArea>

                <div className="p-4 bg-slate-50 border-t">
                    <form onSubmit={handleSubmit} className="flex gap-2 max-w-3xl mx-auto">
                        <Input
                            value={input}
                            onChange={(e: any) => setInput(e.target.value)}
                            placeholder="Ask about your venture..."
                            disabled={isLoading}
                            className="flex-1 bg-white"
                        />
                        <Button type="submit" disabled={isLoading || !input.trim()}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </form>
                </div>
            </Card>
        </div>
    );
}
