# Hand Gesture Tracker - Backend

Python backend for real-time hand gesture tracking using MediaPipe and OpenCV.

## 🛠️ Tech Stack

- **Python 3.13**
- **Flask** - Web server with CORS support
- **Flask-SocketIO** - WebSocket for real-time communication
- **MediaPipe** - Hand tracking ML model
- **OpenCV** - Video capture and processing

## 📁 Structure

```
backend/
├── app.py              # Flask server with WebSocket endpoints
├── HandTracker.py      # MediaPipe hand tracking implementation
├── .venv/              # Python virtual environment
└── test_*.py           # Test files for debugging
```

## 🚀 Getting Started

### 1. Activate Virtual Environment

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install flask flask-socketio flask-cors opencv-python mediapipe
```

### 3. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5000` with WebSocket support.

## 🔌 API Endpoints

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Establish connection |
| `start_tracking` | Client → Server | Start hand tracking |
| `stop_tracking` | Client → Server | Stop hand tracking |
| `hand_data` | Server → Client | Real-time hand landmark data |
| `frame` | Server → Client | Processed video frame (base64) |

## 📊 Hand Data Format

```json
{
  "landmarks": [
    {"x": 0.5, "y": 0.5, "z": 0.0},
    // ... 21 landmarks total
  ],
  "gesture": "open_palm",
  "confidence": 0.95
}
```
