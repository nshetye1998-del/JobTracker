import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { MessageCircle, Send, Sparkles, X } from 'lucide-react';

const ChatPanel = ({ onClose }) => {
    const [messages, setMessages] = useState([
        { role: 'system', content: 'Hello! I am your CareerOps Agent. You can ask me for stats or to research a company.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);

        let intent = 'unknown';
        let params = {};

        if (userMsg.toLowerCase().includes('stats') || userMsg.toLowerCase().includes('status')) {
            intent = 'stats_today';
        } else if (userMsg.toLowerCase().includes('research')) {
            intent = 'research_company';
            const company = userMsg.split('research')[1]?.trim();
            if (company) params = { company };
        } else if (userMsg.toLowerCase().includes('summary')) {
            intent = 'summarize_last';
        } else {
            intent = 'natural_language';
            params = { message: userMsg };
        }

        try {
            const res = await axios.post('http://localhost:8004/intent', {
                intent,
                parameters: params
            });

            setMessages(prev => [...prev, { role: 'system', content: res.data.response }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'system', content: 'Sorry, I encountered an error processing your request.' }]);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 flex flex-col h-[500px] overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-white/20 backdrop-blur-sm p-2 rounded-lg">
                            <MessageCircle className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-white">AI Assistant</h3>
                            <p className="text-xs text-blue-100">Ask me anything</p>
                        </div>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-white" />
                        </button>
                    )}
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl p-4 ${
                            msg.role === 'user'
                                ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white'
                                : 'bg-slate-800/50 backdrop-blur-sm border border-slate-700 text-slate-200'
                        }`}>
                            {msg.role === 'system' && (
                                <Sparkles className="w-4 h-4 text-purple-400 mb-2" />
                            )}
                            <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-4">
                            <div className="flex gap-2 items-center">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                </div>
                                <span className="text-xs text-slate-400 ml-2">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900/30">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask me anything..."
                        className="flex-1 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-4 py-3 rounded-xl disabled:opacity-50 transition-all flex items-center gap-2 font-semibold shadow-lg hover:shadow-blue-500/50"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ChatPanel;
