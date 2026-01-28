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

    if (!video) return <div className="chat-container empty">Select a video to start.</div>;

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div>
                    <h3>{video.filename}</h3>
                    <small className="text-muted">ID: {videoId?.substring(0, 8)}...</small>
                </div>
                <div className="status-badge">
                    <div className="status-dot"></div>
                    <span>Active</span>
                </div>
            </div>

            <div className="video-player-container">
                <video
                    src={`http://localhost:8000/videos/${encodeURIComponent(video.filename)}`}
                    controls
                    className="video-player"
                />
            </div>

            <div className="messages-area">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        {msg.role === 'ai' ? <Bot className="avatar" /> : <User className="avatar" />}
                        <div className="content">
                            {msg.content}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="message ai">
                        <Bot className="avatar" />
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
