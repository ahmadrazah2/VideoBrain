import os
import sys
import hashlib
import base64
import cv2
import whisper
import chromadb
import tempfile
import subprocess
import torch
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# --- Mac Stability Fixes (for nested processes/subprocesses if any) ---
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

# Add conda environment's bin to PATH so it can find ffmpeg
conda_bin = os.path.join(sys.prefix, "bin")
if conda_bin not in os.environ["PATH"]:
    os.environ["PATH"] = conda_bin + os.pathsep + os.environ["PATH"]

# --- Configuration & Initialization ---

# 1. Vision LLM
# Vision Client (OpenAI-compatible)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Embedding Model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Vector Database
db_client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "chroma_db_video"))
video_collection = db_client.get_or_create_collection(
    name=os.getenv("CHROMA_DB_COLLECTION", "video_collection"),
    metadata={"hnsw:space": "cosine"}
)

# 4. Whisper Model (Lazy loaded)
whisper_model = None
FRAME_SAMPLE_RATE = int(os.getenv("FRAME_SAMPLE_RATE", 10))


# --- Helper Functions ---

def get_video_id(video_path: str) -> str:
    """Creates a unique ID for the video based on its content."""
    hasher = hashlib.sha256()
    with open(video_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("⏳ Loading Whisper base model...")
        whisper_model = whisper.load_model("base", device="cpu")
    return whisper_model

def extract_audio_ffmpeg(video_path: str) -> str:
    """Extract mono 16kHz audio to a temp MP3 using ffmpeg."""
    fd, audio_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "libmp3lame",
        "-ar", "16000", "-ac", "1", "-y",
        audio_path
    ]

    print(f"🎬 Extracting audio from {video_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    return audio_path

def transcribe_audio_whisper(audio_path: str) -> List[Dict[str, Any]]:
    """Transcribe audio using Whisper."""
    model = get_whisper_model()
    print("📝 Transcribing with Whisper...")
    # fp16=False is necessary on Mac CPU
    result = model.transcribe(audio_path, fp16=False, language='en')
    return result.get("segments", [])

def get_visual_descriptions(video_path: str) -> List[Dict[str, Any]]:
    """Samples frames from a video and generates visual descriptions using Gemini."""
    print(f"🖼️ Starting visual frame description for {video_path}...")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps else 0
    
    visual_docs = []
    
    for i in range(0, int(duration), FRAME_SAMPLE_RATE):
        cap.set(cv2.CAP_PROP_POS_MSEC, i * 1000)
        ret, frame = cap.read()
        if not ret:
            continue
            
        _, buffer = cv2.imencode('.jpeg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        response = openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this video frame in detail. What is happening? What objects are present? What is the context?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        description = response.choices[0].message.content
        
        visual_docs.append({
            "content": description,
            "timestamp": i,
            "timestamp_formatted": f"{int(i // 60)}:{int(i % 60):02d}"
        })
        print(f"  - Described frame at {i}s: '{description[:50]}...'")

    cap.release()
    print("✅ Visual description complete.")
    return visual_docs

def store_in_chromadb(video_id: str, video_path: str, audio_segments: List, visual_descriptions: List):
    """Stores audio and visual data chunks in ChromaDB with appropriate metadata."""
    print(f"💾 Storing multimodal data in ChromaDB for video_id: {video_id}...")
    documents = []
    metadatas = []
    ids = []
    
    # Process audio segments
    for i, seg in enumerate(audio_segments):
        start = seg['start']
        documents.append(seg['text'].strip())
        metadatas.append({
            "video_id": video_id,
            "timestamp": start,
            "timestamp_formatted": f"{int(start // 60)}:{int(start % 60):02d}",
            "type": "audio",
            "video_path": video_path
        })
        ids.append(f"{video_id}_audio_{i}")

    # Process visual descriptions
    for i, desc in enumerate(visual_descriptions):
        documents.append(desc['content'])
        metadatas.append({
            "video_id": video_id,
            "timestamp": desc['timestamp'],
            "timestamp_formatted": desc['timestamp_formatted'],
            "type": "visual",
            "video_path": video_path
        })
        ids.append(f"{video_id}_visual_{i}")
        
    if documents:
        embedded_docs = embedding_model.embed_documents(documents)
        video_collection.add(
            embeddings=embedded_docs,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Stored {len(documents)} context blocks in ChromaDB.")
    else:
        print("No documents to store.")

def process_and_ingest_video(video_path: str) -> str:
    """Runs the full pipeline: process a video and store its data."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")

    video_id = get_video_id(video_path)
    
    # Check if video has already been processed
    existing = video_collection.get(where={"video_id": video_id}, limit=1)
    if existing and existing['ids']:
        print(f"✅ Video {video_id} has already been processed. Skipping ingestion.")
        return video_id
        
    # 1. Audio Processing
    audio_temp = None
    audio_segments = []
    try:
        audio_temp = extract_audio_ffmpeg(video_path)
        audio_segments = transcribe_audio_whisper(audio_temp)
    finally:
        if audio_temp and os.path.exists(audio_temp):
            os.remove(audio_temp)

    # 2. Visual Processing
    visual_descriptions = get_visual_descriptions(video_path)
    
    # 3. Storage
    store_in_chromadb(video_id, video_path, audio_segments, visual_descriptions)
    
    return video_id
