import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const ChatInterface = ({ video }) => {
    const [messages, setMessages] = useState([
        { role: 'ai', content: 'Video processed! Ask me anything about it.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const videoId = video?.id;

    // Use a pseudo-random thread ID for this session
    const [threadId] = useState(() => Math.random().toString(36).substring(7));

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading || !videoId) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/chat', {
                message: userMsg,
                video_id: videoId,
                thread_id: threadId
            });

            setMessages(prev => [...prev, { role: 'ai', content: response.data.response }]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: 'ai', content: 'Error: Could not get response from agent.' }]);
        } finally {
            setLoading(false);
        }
    };

    if (!video) return <div className="chat-container">Select a video to start.</div>;

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{video.filename}</h3>
                    <small className="text-muted">ID: {videoId?.substring(0, 8)}...</small>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }}></div>
                    <span style={{ fontSize: '0.875rem', fontWeight: 500, color: '#10b981' }}>Active</span>
                </div>
            </div>

            <div className="video-player-container" style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--border-color)', background: '#f8fafc', display: 'flex', justifyContent: 'center' }}>
                <video
                    src={`http://localhost:8000/videos/${encodeURIComponent(video.filename)}`}
                    controls
                    style={{
                        maxWidth: '480px',
                        width: '100%',
                        borderRadius: '0.75rem',
                        backgroundColor: '#000',
                        boxShadow: 'var(--shadow-sm)'
                    }}
                />
            </div>

            <div className="messages-area">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className="content">
                            {msg.content}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="message ai">
                        <div className="content typing-indicator">
                            <Loader2 size={16} className="spinner" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area-container">
                <form onSubmit={handleSend} className="input-area">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Message VideoBrain..."
                        disabled={loading}
                    />
                    <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
                        <Send size={18} />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
