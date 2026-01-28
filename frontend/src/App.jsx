import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import VideoUploader from './components/VideoUploader';
import ChatInterface from './components/ChatInterface';

function App() {
    const [videos, setVideos] = useState([]);
    const [activeVideo, setActiveVideo] = useState(null);
    const [showUploader, setShowUploader] = useState(true);

    const handleVideoProcessed = (videoMetadata) => {
        setVideos(prev => [...prev, videoMetadata]);
        setActiveVideo(videoMetadata);
        setShowUploader(false);
    };

    const handleNewChat = () => {
        setActiveVideo(null);
        setShowUploader(true);
    };

    const handleVideoSelect = (id) => {
        const video = videos.find(v => v.id === id);
        setActiveVideo(video);
        setShowUploader(false);
    };

    return (
        <div className="app-container">
            <Sidebar
                videos={videos}
                activeVideoId={activeVideo?.id}
                onVideoSelect={handleVideoSelect}
                onNewChat={handleNewChat}
            />

            <main className="main-content">
                {showUploader || !activeVideo ? (
                    <VideoUploader
                        onVideoProcessed={handleVideoProcessed}
                        onCancel={videos.length > 0 ? () => setShowUploader(false) : null}
                    />
                ) : (
                    <ChatInterface video={activeVideo} key={activeVideo.id} />
                )}
            </main>
        </div>
    );
}

export default App;
