import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User } from 'lucide-react';

export default function RagChat({ bookId, bookTitle }) {
    const [question, setQuestion] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory]);

    const askQuestion = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;

        const currentQuestion = question;
        setQuestion('');
        
        // Add user question to history
        setChatHistory(prev => [...prev, { role: 'user', content: currentQuestion }]);
        // Add empty AI response placeholder to history
        setChatHistory(prev => [...prev, { role: 'ai', content: '' }]);
        setIsStreaming(true);

        try {
            const response = await fetch('http://localhost:8000/api/rag/query/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: currentQuestion, book_id: bookId })
            });

            if (!response.ok) throw new Error("Network response was not ok");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiResponse = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const text = line.slice(6).replace(/\\n/g, '\n');
                        aiResponse += text;
                        
                        // Update only the last message (the AI's current response)
                        setChatHistory(prev => {
                            const newHistory = [...prev];
                            newHistory[newHistory.length - 1].content = aiResponse;
                            return newHistory;
                        });
                    }
                }
            }
        } catch (error) {
            console.error("Failed to stream:", error);
            setChatHistory(prev => {
                const newHistory = [...prev];
                newHistory[newHistory.length - 1].content = "⚠️ Sorry, the AI connection was interrupted.";
                return newHistory;
            });
        } finally {
            setIsStreaming(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[600px]">
            {/* Chat Header */}
            <div className="bg-gray-900 px-6 py-4">
                <h3 className="text-lg font-bold text-white flex items-center">
                    <Bot className="w-5 h-5 mr-2 text-indigo-400" /> 
                    Ask about {bookTitle}
                </h3>
            </div>

            {/* Chat Messages Area */}
            <div className="flex-grow p-6 overflow-y-auto bg-gray-50 space-y-6">
                {chatHistory.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
                        <Bot className="w-12 h-12 text-gray-300" />
                        <p>Ask a question to search the contents of this book.</p>
                    </div>
                ) : (
                    chatHistory.map((msg, index) => (
                        <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-indigo-600 ml-3' : 'bg-gray-800 mr-3'}`}>
                                    {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
                                </div>
                                <div className={`px-5 py-4 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white shadow-sm border border-gray-100 text-gray-800 rounded-tl-none'}`}>
                                    {msg.role === 'user' ? (
                                        <p>{msg.content}</p>
                                    ) : (
                                        <div className="prose prose-sm max-w-none">
                                            <ReactMarkdown>{msg.content || '...'}</ReactMarkdown>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-gray-100">
                <form onSubmit={askQuestion} className="relative flex items-center">
                    <input 
                        type="text" 
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="e.g., How does the story resolve?"
                        className="w-full pl-5 pr-14 py-4 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
                        disabled={isStreaming}
                    />
                    <button 
                        type="submit" 
                        disabled={isStreaming || !question.trim()}
                        className="absolute right-2 p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </div>
    );
}