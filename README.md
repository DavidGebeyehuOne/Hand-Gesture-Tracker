# 🖐️ Hand Gesture Tracker Ultra Pro (Essential Edition)

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-00A98F?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev/)
[![Status](https://img.shields.io/badge/Gestures-Top_10-6366f1?style=for-the-badge)](https://github.com/yourusername/Hand-Gesture-Tracker)
[![UI](https://img.shields.io/badge/UI-CustomTkinter-0059b3?style=for-the-badge&logo=python&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)

A refined, high-precision hand tracking system optimized for **Python 3.13**. This edition focuses on the **Top 10 Essential Gestures**, delivering lightning-fast detection and a minimalist "Pure Noir" aesthetic.

---

## 🔥 Essential Precision

- 🎯 **Optimized Top 10**: We've stripped away the noise to focus on the 10 most common and accurate gestures.
- 🌑 **Pure Noir Overlay**: All on-screen feedback—including FPS and results—is rendered in **Deep Black (0, 0, 0)** for a professional, high-contrast look.
- 👐 **Dual-Hand Mastery**: Simultaneous tracking for **Heart Shape** and **Prayer** gestures.
- 🚀 **Python 3.13 Ready**: Zero-configuration support for the latest Python ecosystem using MediaPipe Tasks.

---

## 🎬 The Essential 10 Library

| Gesture | Emoji | Name | Interaction |
| :--- | :---: | :--- | :--- |
| **Open Hand** | ✋ | Stop / Hello | Individual |
| **Thumbs Up** | � | Approval | Individual |
| **Thumbs Down**| � | Disapproval | Individual |
| **Peace Sign** | ✌️ | Peace / Victory | Individual |
| **OK Sign** | 👌 | Perfection | Individual |
| **Pointing** | ☝️ | Focus / One | Individual |
| **Rock On** | 🤘 | Culture / Energy | Individual |
| **Fist** | 👊 | Solidarity | Individual |
| **Heart Shape**| � | Love / Care | **Dual-Hand** |
| **Prayer** | 🙏 | Namaste / Respect| **Dual-Hand** |

---

## 🛠️ Technology Stack

### **Backend Engine**
*   **MediaPipe Tasks API**: Modern 2025 Vision pipeline.
*   **Noir UI**: CustomTkinter interface with pure black backgrounds (`#000000`).
*   **Deep Contrast Overlays**: All computer vision labels (FPS, Hand Labels, Gesture Names) are rendered in black for a perfect viewing experience.

### **Frontend Console**
*   **Next.js 16**: High-performance web framework.
*   **Tailwind CSS 4**: Next-gen utility styling.

---

## 🚀 Installation & Setup

### 1. Requirements
*   **Python 3.13+**
*   **Webcam**

### 2. Backend Installation (Desktop)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install mediapipe opencv-python customtkinter pillow numpy
```

---

## 💻 Usage

### Launch Desktop Tracker
```bash
cd backend
python app.py
```
- **Noir Design**: The window and video elements are color-unified for professional grade monitoring.
- **Top 10 Logic**: Detection is now sharper and less prone to false triggers.

---

## � Project Structure

```bash
Hand-Gesture-Tracker/
├── 📂 backend/                # Desktop Application
│   ├── app.py                 # "Pure Black" UI Controller
│   ├── HandTracker.py         # Top 10 Optimized Engine
│   └── hand_landmarker.task   # ML Model Asset
├── 📂 frontend/               # Next.js Web Application
└── README.md                  # Unified Documentation
```

---

## 📄 License
Distributed under the MIT License.

<p align="center">
  <br/>
  <b>Precision Tracking. Minimalist Design. Essential Control.</b>
</p>
