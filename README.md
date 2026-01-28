### **Multimodal RAG-Based Video Reasoning Agent**

> Upload Zoom or YouTube videos and chat with them.
> VideoBrain analyzes videos frame-by-frame using vision models, transcribes speech with timestamps, stores multimodal knowledge in a RAG pipeline, and answers questions with grounded, time-aware reasoning.

---

## 📺 Video Demo

<p align="center">
  <video src="https://github.com/user-attachments/assets/4f11695b-de14-4e76-bc44-4f4272319d3e" width="100%" controls></video>
</p>

---

## 🚀 What VideoBrain Does

VideoBrain enables **deep understanding of videos** by combining **visual perception**, **audio transcription**, and **retrieval-augmented reasoning**.

Instead of keyword search, it lets you **ask natural questions** and get answers grounded in **what was said**, **what was shown**, and **when it happened**.

---

## 🧩 Core Capabilities

* 📹 Upload **Zoom recordings or YouTube videos**
* 🖼️ Extract frames at fixed intervals and generate **frame-by-frame visual descriptions**
* 🎙️ Transcribe audio with **precise timestamps**
* 🧠 Store visual + audio knowledge in a **multimodal RAG index**
* 💬 Ask questions and receive **timestamp-grounded answers**

---

## 🏗️ Architecture Overview

The project is divided into two main components: a **FastAPI backend** and a **React frontend**.

### Backend

The backend is responsible for processing the videos, storing the data, and handling the chat logic.

*   **`main.py`**: The main entry point of the backend application. It defines the FastAPI server and the API endpoints for video upload and chat.
*   **`core/video_processor.py`**: This file contains the core logic for processing videos. It extracts audio, transcribes it using Whisper, generates visual descriptions using a vision LLM, and stores the multimodal data in ChromaDB.
*   **`core/agent.py`**: This file defines the AI agent that answers user questions. It uses LangGraph to create a stateful agent that can retrieve documents from ChromaDB, grade their relevance, rewrite queries, and generate answers using a large language model.

### Frontend

The frontend provides the user interface for uploading videos and interacting with the AI agent.

*   **`App.jsx`**: The main component of the frontend application. It manages the overall layout and state of the UI.
*   **`components/VideoUploader.jsx`**: This component handles the video upload process, sending the video to the backend's `/upload` endpoint.
*   **`components/ChatInterface.jsx`**: This component provides the chat interface, sending user messages to the backend's `/chat` endpoint and displaying the conversation.
*   **`components/Sidebar.jsx`**: This component displays the list of uploaded videos and allows the user to switch between them.

---

## 🛠️ Tech Stack

* **Vision Model**: Qwen2.5-VL
* **Speech Recognition**: OpenAI Whisper
* **Reasoning LLM**: Llama-3.3-70B (via Groq API)
* **Vector Database**: ChromaDB
* **Agent Orchestration**: LangGraph
* **Backend**: FastAPI
* **Frontend**: React
* **Video Processing**: FFmpeg, OpenCV

---

## 🚀 Getting Started

### 1. Prerequisites
* **FFmpeg** installed on your system.
* **Conda** for environment management.
* API Keys for: **OpenAI** (for Whisper).

### 2. Setup Backend
```bash
cd backend
conda create -n video_brain python=3.10
conda activate video_brain
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the `backend` directory:
```env
OPENAI_API_KEY="your-openai-api-key"
```

### 4. Run the Backend
```bash
cd backend
python main.py
```
*API will be available at `http://localhost:8000`*

### 5. Setup and Run the Frontend
```bash
cd frontend
npm install
npm run dev
```
*UI will be available at `http://localhost:5173`*

---

## 🎯 Use Cases

* 📚 Lecture & course video understanding
* 🧑💻 Zoom meeting analysis
* 🎥 Technical tutorial search
* 🧠 Research & educational AI agents
* 🗂️ Long-form video knowledge extraction

---

## 🔮 Future Improvements

* OCR from slides and code screens
* Scene segmentation & shot detection
* Temporal attention across frames
* Multi-video cross-RAG reasoning
