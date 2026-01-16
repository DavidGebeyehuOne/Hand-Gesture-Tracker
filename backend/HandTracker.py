"""
Hand Tracker using MediaPipe Tasks API (Python 3.13 compatible)
Optimized for Top 10 Common Gestures with Pure Black Aesthetics.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import time
from pathlib import Path

# MediaPipe Tasks API imports
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class HandGesture:
    name: str
    color: Tuple[int, int, int]
    confidence: float


class HandTracker:
    """
    Hand tracking and gesture recognition using MediaPipe Tasks API.
    Compatible with Python 3.13+
    """
    
    # Hand landmark connections for drawing
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),      # Index finger
        (0, 9), (9, 10), (10, 11), (11, 12), # Middle finger
        (0, 13), (13, 14), (14, 15), (15, 16), # Ring finger
        (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
        (5, 9), (9, 13), (13, 17)            # Palm
    ]
    
    # Landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20
    
    def __init__(self,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5):
        
        # Find the model file
        model_path = self._find_model_path()
        
        # Create HandLandmarker options
        base_options = python.BaseOptions(model_asset_path=str(model_path))
        
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # Landmark groups
        self.palm_landmarks = [0, 1, 5, 9, 13, 17]
        self.finger_tips = [4, 8, 12, 16, 20]
        self.finger_pips = [2, 6, 10, 14, 18]
        
        # FPS tracking
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.frame_timestamp = 0
        
        # Colors for drawing (Default)
        self.landmark_color = (0, 255, 0)      # Green
        self.connection_color = (255, 255, 255) # White
        self.tip_color = (0, 0, 255)            # Red for fingertips
    
    def _find_model_path(self) -> Path:
        """Find the hand_landmarker.task model file"""
        possible_paths = [
            Path(__file__).parent / "hand_landmarker.task",
            Path.cwd() / "hand_landmarker.task",
            Path.cwd() / "backend" / "hand_landmarker.task",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            "Could not find hand_landmarker.task model file."
        )
    
    def get_landmark_coordinates(self, landmarks, idx: int) -> np.ndarray:
        """Get landmark coordinates as numpy array"""
        lm = landmarks[idx]
        return np.array([lm.x, lm.y, lm.z])
    
    def calculate_finger_angles(self, landmarks) -> Dict[str, float]:
        """Calculate the angle at each finger joint"""
        angles = {}
        
        finger_landmarks = {
            'Thumb': [2, 3, 4],
            'Index': [5, 6, 8],
            'Middle': [9, 10, 12],
            'Ring': [13, 14, 16],
            'Pinky': [17, 18, 20]
        }
        
        for finger, points in finger_landmarks.items():
            p1 = self.get_landmark_coordinates(landmarks, points[0])
            p2 = self.get_landmark_coordinates(landmarks, points[1])
            p3 = self.get_landmark_coordinates(landmarks, points[2])
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calculate angle
            dot_product = np.dot(v1, v2)
            magnitudes = np.linalg.norm(v1) * np.linalg.norm(v2)
            
            if magnitudes > 0:
                angle = np.degrees(np.arccos(np.clip(dot_product / magnitudes, -1.0, 1.0)))
            else:
                angle = 0
            
            angles[finger] = angle
        
        return angles
    
    def is_finger_extended(self, landmarks, finger_tip: int, finger_pip: int, 
                           finger_mcp: int) -> bool:
        """Check if a finger is extended (straightened)"""
        tip = self.get_landmark_coordinates(landmarks, finger_tip)
        pip = self.get_landmark_coordinates(landmarks, finger_pip)
        
        # Finger is extended if tip is further from wrist than pip
        wrist = self.get_landmark_coordinates(landmarks, 0)
        return np.linalg.norm(tip - wrist) > np.linalg.norm(pip - wrist)
    
    def get_finger_states(self, landmarks) -> Dict[str, bool]:
        """Get the extended/closed state of each finger"""
        states = {}
        
        # Thumb: index-mcp to thumb-tip distance
        tip = self.get_landmark_coordinates(landmarks, 4)
        mcp = self.get_landmark_coordinates(landmarks, 5)
        states['Thumb'] = np.linalg.norm(tip - mcp) > 0.08
        
        # Other fingers
        finger_data = {
            'Index': (8, 6, 5),
            'Middle': (12, 10, 9),
            'Ring': (16, 14, 13),
            'Pinky': (20, 18, 17)
        }
        
        for finger, (tip, pip, mcp) in finger_data.items():
            states[finger] = self.is_finger_extended(landmarks, tip, pip, mcp)
        
        return states
    
    def detect_gesture(self, landmarks, is_right: bool, frame_pos: Tuple[float, float]) -> Optional[HandGesture]:
        """Detect individual hand gestures (Top 8)"""
        states = self.get_finger_states(landmarks)
        
        # Refined Thumb Logic
        thumb_tip = self.get_landmark_coordinates(landmarks, 4)
        thumb_mcp = self.get_landmark_coordinates(landmarks, 2)
        index_mcp = self.get_landmark_coordinates(landmarks, 5)
        middle_pip = self.get_landmark_coordinates(landmarks, 10)
        
        # Check if thumb is strongly abducted (sticking out) vs folded over
        # If thumb tip is close to middle finger PIP, it's likely a fist
        is_thumb_over_fingers = np.linalg.norm(thumb_tip - middle_pip) < 0.1
        
        # Override thumb state if it's wrapped over fingers
        if is_thumb_over_fingers:
            states['Thumb'] = False

        def all_ext(*fingers): return all(states[f] for f in fingers)
        def all_closed(*fingers): return all(not states[f] for f in fingers)

        # 1. OPEN HAND / STOP
        if all_ext('Index', 'Middle', 'Ring', 'Pinky'):
            return HandGesture("Open Hand", (0, 0, 0), 0.9)

        # 2. FIST (Check first to avoid Thumbs Down misfires)
        if all_closed('Index', 'Middle', 'Ring', 'Pinky') and (not states['Thumb'] or is_thumb_over_fingers):
            return HandGesture("Fist", (0, 0, 0), 0.9)

        # 3. THUMBS UP
        if states['Thumb'] and not is_thumb_over_fingers and all_closed('Index', 'Middle', 'Ring', 'Pinky'):
            if landmarks[4].y < landmarks[3].y:
                return HandGesture("Thumbs Up", (0, 0, 0), 0.9)

        # 4. THUMBS DOWN
        if states['Thumb'] and not is_thumb_over_fingers and all_closed('Index', 'Middle', 'Ring', 'Pinky'):
            if landmarks[4].y > landmarks[3].y:
                return HandGesture("Thumbs Down", (0, 0, 0), 0.9)

        # 5. PEACE SIGN vs LUCK
        if states['Index'] and states['Middle'] and all_closed('Ring', 'Pinky'):
            # Check distance between tips to distinguish Peace vs Luck
            tip8 = self.get_landmark_coordinates(landmarks, 8)
            tip12 = self.get_landmark_coordinates(landmarks, 12)
            dist_tips = np.linalg.norm(tip8 - tip12)
            
            # If fingers are very close/crossed, it's Luck
            if dist_tips < 0.05:
                return HandGesture("Luck", (0, 0, 0), 0.9)
            # If fingers are spread apart, it's Peace
            else:
                return HandGesture("Peace Sign", (0, 0, 0), 0.9)

        # 6. OK SIGN
        tip4 = self.get_landmark_coordinates(landmarks, 4)
        tip8 = self.get_landmark_coordinates(landmarks, 8)
        if np.linalg.norm(tip4 - tip8) < 0.05 and all_ext('Middle', 'Ring', 'Pinky'):
            return HandGesture("OK Sign", (0, 0, 0), 0.9)

        # 7. POINTING
        if states['Index'] and all_closed('Middle', 'Ring', 'Pinky'):
            return HandGesture("Pointing", (0, 0, 0), 0.9)

        # 8. ROCK ON
        if states['Index'] and states['Pinky'] and all_closed('Middle', 'Ring'):
            return HandGesture("Rock On", (0, 0, 0), 0.9)

        return None

    def detect_two_hand_gestures(self, hands_data: List[Dict]) -> Optional[HandGesture]:
        """Detect essential two-hand gestures (Top 2)"""
        if len(hands_data) < 2: return None
        
        h1, h2 = hands_data[0], hands_data[1]
        p1 = self.get_landmark_coordinates(h1['landmarks'], 0)
        p2 = self.get_landmark_coordinates(h2['landmarks'], 0)
        dist = np.linalg.norm(p1 - p2)

        # 9. HEART SHAPE
        t1, t2 = h1['landmarks'][4], h2['landmarks'][4]
        i1, i2 = h1['landmarks'][8], h2['landmarks'][8]
        if np.linalg.norm(np.array([t1.x, t1.y]) - np.array([t2.x, t2.y])) < 0.1 and \
           np.linalg.norm(np.array([i1.x, i1.y]) - np.array([i2.x, i2.y])) < 0.1:
            return HandGesture("Heart Shape", (0, 0, 0), 0.9)

        # 10. CROSSED FINGERS / LUCK
        # Detect if index and middle fingers are crossed
        # This is a single-hand gesture, but we check if EITHER hand is doing it
        
        def check_crossed(hand_data):
            lms = hand_data['landmarks']
            # Get index and middle tips
            i_tip = self.get_landmark_coordinates(lms, 8)
            m_tip = self.get_landmark_coordinates(lms, 12)
            
            # Distance between tips should be very small (crossed)
            crossed_dist = np.linalg.norm(i_tip - m_tip)
            
            states = self.get_finger_states(lms)
            # Index and Middle extend, others closed
            if states['Index'] and states['Middle'] and not states['Ring'] and not states['Pinky']:
                if crossed_dist < 0.05: # Very close/crossed
                    return True
            return False

        if check_crossed(h1):
            return HandGesture("Luck", (0, 0, 0), 0.9)
        if check_crossed(h2):
            return HandGesture("Luck", (0, 0, 0), 0.9)

        return None

    def draw_landmarks(self, image: np.ndarray, landmarks, 
                      image_width: int, image_height: int) -> None:
        """Draw hand landmarks and connections on the image"""
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = landmarks[start_idx]
            end = landmarks[end_idx]
            start_point = (int(start.x * image_width), int(start.y * image_height))
            end_point = (int(end.x * image_width), int(end.y * image_height))
            cv2.line(image, start_point, end_point, self.connection_color, 2)
        
        for i, lm in enumerate(landmarks):
            x, y = int(lm.x * image_width), int(lm.y * image_height)
            if i in self.finger_tips:
                cv2.circle(image, (x, y), 8, self.tip_color, -1)
            else:
                cv2.circle(image, (x, y), 5, self.landmark_color, -1)
    
    def draw_labeled_box(self, image: np.ndarray, text: str, position: Tuple[int, int], 
                        color: Tuple[int, int, int]) -> None:
        """Draw a labeled box with gesture information in Black"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        padding = 10
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x, y = position
        cv2.rectangle(image, (x - padding, y - text_height - padding), 
                     (x + text_width + padding, y + padding), (0, 0, 0), 2)
        cv2.putText(image, text, (x, y), font, font_scale, (0, 0, 0), thickness)

    def draw_fps(self, image: np.ndarray) -> None:
        """Draw FPS counter in black"""
        self.new_frame_time = time.time()
        fps = 1 / (self.new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
        self.prev_frame_time = self.new_frame_time
        h, _, _ = image.shape
        self.draw_labeled_box(image, f"FPS: {int(fps)}", (10, h - 30), (0, 0, 0))
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.frame_timestamp += 33
        results = self.detector.detect_for_video(mp_image, self.frame_timestamp)
        h, w, _ = frame.shape
        
        hands_data = []
        if results.hand_landmarks:
            for i, (lms, handedness) in enumerate(zip(results.hand_landmarks, results.handedness)):
                is_right = handedness[0].category_name == "Right"
                hands_data.append({'landmarks': lms, 'is_right': is_right})
                self.draw_landmarks(frame, lms, w, h)

        joint_gesture = self.detect_two_hand_gestures(hands_data)
        if joint_gesture:
            self.draw_labeled_box(frame, f"BOTH: {joint_gesture.name}", (w//2 - 100, 50), (0, 0, 0))
        else:
            for i, data in enumerate(hands_data):
                lms = data['landmarks']
                gesture = self.detect_gesture(lms, data['is_right'], (lms[0].x, lms[0].y))
                if gesture:
                    hand_label = "Right" if data['is_right'] else "Left"
                    self.draw_labeled_box(frame, f"{hand_label}: {gesture.name}", (10, 40 + i * 60), (0, 0, 0))
        
        self.draw_fps(frame)
        return frame
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'detector'):
            self.detector.close()


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened(): cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return
    
    tracker = HandTracker()
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success: break
            frame = tracker.process_frame(frame)
            cv2.imshow('Hand Tracking - MediaPipe Tasks API', frame)
            if cv2.waitKey(1) & 0xFF in [27, ord('q')]: break
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()