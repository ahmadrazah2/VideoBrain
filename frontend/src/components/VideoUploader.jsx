import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileVideo, Loader2 } from 'lucide-react';

const VideoUploader = ({ onVideoProcessed, onCancel }) => {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreviewUrl(URL.createObjectURL(selectedFile));
            setError('');
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://localhost:8000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            onVideoProcessed({
                id: response.data.video_id,
                filename: file.name
            });
        } catch (err) {
            console.error(err);
            setError('Failed to upload/process video. Ensure backend is running.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="uploader-overlay">
            <h2><Upload className="icon" /> New Video Analysis</h2>
            <p className="subtitle">Upload a video to start a new AI-powered conversation.</p>

            <div className="drop-zone">
                <input
                    type="file"
                    accept="video/*"
                    onChange={handleFileChange}
                    id="file-input"
                    className="file-input"
                />
                <label htmlFor="file-input" className="file-label" style={{ padding: file ? '1rem' : '4rem 2rem' }}>
                    {file ? (
                        <div className="file-selected" style={{ width: '100%' }}>
                            {previewUrl && (
                                <video
                                    src={previewUrl}
                                    style={{ width: '100%', maxHeight: '200px', borderRadius: '0.5rem', marginBottom: '1rem' }}
                                />
                            )}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
                                <FileVideo size={20} className="file-icon" />
                                <span style={{ fontWeight: 600 }}>{file.name}</span>
                            </div>
                        </div>
                    ) : (
                        <>
                            <Upload size={48} />
                            <span>Click or drag video here to upload</span>
                        </>
                    )}
                </label>
            </div>

            {error && <p className="error-msg" style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>}

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                {onCancel && (
                    <button onClick={onCancel} className="secondary-btn" style={{ padding: '0.75rem 1.5rem', borderRadius: '0.5rem', cursor: 'pointer', border: '1px solid #e2e8f0', background: 'white' }}>
                        Cancel
                    </button>
                )}
                <button
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    className="primary-btn"
                >
                    {uploading ? (
                        <>
                            <Loader2 className="spinner" /> Processing...
                        </>
                    ) : 'Start Analysis'}
                </button>
            </div>
        </div>
    );
};

export default VideoUploader;
