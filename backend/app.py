"""
Flask server with WebSocket endpoints for real-time hand gesture tracking.
Replaces the desktop GUI app intended for local use, resolving tkinter deployment errors on Render.
"""

import os
import base64
import numpy as np
import cv2
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from HandTracker import HandTracker

app = Flask(__name__)
# Enable CORS for the Flask app (for REST APIs if any)
CORS(app, resources={r"/*": {"origins": "*"}})

# Enable CORS for SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize global hand tracker
tracker = HandTracker()

@app.route("/")
def index():
    return jsonify({"status": "Hand Tracking Server is running!"})

@socketio.on("connect")
def on_connect():
    print("Client connected")
    emit("status", {"data": "Connected to Server"})

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected")

@socketio.on("frame")
def handle_frame(data):
    """
    Receive base64 video frame from client, process it, and send back base64 annotated frame.
    """
    try:
        image_data = data
        # Handle Data URL scheme if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
            
        decoded = base64.b64decode(image_data)
        np_data = np.frombuffer(decoded, np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        if frame is not None:
            # Process the frame with HandTracker
            processed_frame = tracker.process_frame(frame)
            
            # Encode back to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            _, buffer = cv2.imencode('.jpg', processed_frame, encode_param)
            processed_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emit processed frame back
            emit("frame", {"image": f"data:image/jpeg;base64,{processed_base64}"})
    except Exception as e:
        print(f"Error processing frame: {e}")
        emit("error", {"message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)