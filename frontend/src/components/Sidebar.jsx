import React from 'react';
import { Plus, Video, Sparkles } from 'lucide-react';

const Sidebar = ({ videos, activeVideoId, onVideoSelect, onNewChat }) => {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <h2><Sparkles size={20} /> VideoBrain</h2>
                <button className="new-chat-btn" onClick={onNewChat}>
                    <Plus size={18} /> New Chat
                </button>
            </div>

            <div className="video-list">
                {videos.map((video) => (
                    <div
                        key={video.id}
                        className={`video-item ${activeVideoId === video.id ? 'active' : ''}`}
                        onClick={() => onVideoSelect(video.id)}
                    >
                        <div style={{ width: 32, height: 32, borderRadius: '4px', overflow: 'hidden', background: '#000', flexShrink: 0 }}>
                            <video
                                src={`http://localhost:8000/videos/${encodeURIComponent(video.filename)}#t=1`}
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                        </div>
                        <span className="video-item-title" title={video.filename}>{video.filename}</span>
                    </div>
                ))}
                {videos.length === 0 && (
                    <p className="text-muted" style={{ padding: '1rem', fontSize: '0.875rem' }}>
                        No videos uploaded yet.
                    </p>
                )}
            </div>
        </aside>
    );
};

export default Sidebar;
