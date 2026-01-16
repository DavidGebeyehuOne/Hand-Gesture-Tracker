"""
Hand Gesture Tracker - Premium Modern UI
A beautiful, responsive desktop application for real-time hand tracking
"""

import customtkinter as ctk
import cv2
import PIL.Image, PIL.ImageTk
from pathlib import Path
import threading
from typing import Optional
import os
from HandTracker import HandTracker
import queue
import time
from datetime import datetime


class GradientFrame(ctk.CTkFrame):
    """Custom frame with gradient-like appearance"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class AnimatedButton(ctk.CTkButton):
    """Button with hover animation effects"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.default_color = kwargs.get('fg_color', '#6366f1')
        self.hover_color = kwargs.get('hover_color', '#818cf8')
        

class ModernHandTrackerUI:
    # Color Palette - Pure Deep Black Theme
    COLORS = {
        'bg_dark': '#000000',        # Pure Black
        'bg_card': '#0a0a0a',        # Near Black
        'bg_card_hover': '#111111',
        'primary': '#6366f1',        # Indigo
        'primary_hover': '#818cf8',
        'secondary': '#22d3ee',      # Cyan
        'success': '#10b981',        # Emerald
        'warning': '#f59e0b',        # Amber
        'danger': '#ef4444',         # Red
        'text': '#ffffff',           # Pure White
        'text_muted': '#9ca3af',     # Gray
        'border': '#1f2937',         # Dark border
        'gradient_start': '#6366f1',
        'gradient_end': '#8b5cf6',
    }
    
    def __init__(self):
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("✋ Hand Gesture Tracker")
        self.window.geometry("1400x850")
        self.window.minsize(1200, 700)
        self.window.configure(fg_color=self.COLORS['bg_dark'])

        self.window.configure(fg_color=self.COLORS['bg_dark'])

        # Remove default square icon by generating and setting a transparent .ico
        try:
            icon_path = "transparent.ico"
            if not os.path.exists(icon_path):
                # Create a 16x16 transparent image and save as ICO
                img = PIL.Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                img.save(icon_path, format="ICO")
            
            self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon warning: {e}")
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)

        # Create main container
        self.main_container = ctk.CTkFrame(
            self.window, 
            fg_color=self.COLORS['bg_dark'],
            corner_radius=0
        )
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Build UI components
        self.create_header()
        self.create_main_content()
        self.create_footer()

        # Initialize state
        self.cap: Optional[cv2.VideoCapture] = None
        self.tracker: Optional[HandTracker] = None
        self.is_webcam_active = False
        self.video_thread: Optional[threading.Thread] = None
        self.frame_queue = queue.Queue(maxsize=2)
        
        # Statistics
        self.gestures_detected = 0
        self.session_start_time = None
        self.current_gesture = "None"
        self.gesture_history = []
        
        # Start update loops
        self.update_video_loop()
        self.update_stats_loop()

    def create_header(self):
        """Create the modern header section"""
        header = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.COLORS['bg_card'],
            corner_radius=0,
            height=100
        )
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        # Logo and title section
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=30, pady=20, sticky="w")

        # App icon (emoji-based)
        icon_label = ctk.CTkLabel(
            title_frame,
            text="🖐️",
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(side="left", padx=(0, 15))

        # Title and subtitle
        text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        text_frame.pack(side="left")
        
        title = ctk.CTkLabel(
            text_frame,
            text="Hand Gesture Tracker",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.COLORS['text']
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            text_frame,
            text="Real-time gesture recognition powered by MediaPipe",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLORS['text_muted']
        )
        subtitle.pack(anchor="w")

        # Status indicator
        self.status_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.status_frame.grid(row=0, column=2, padx=30, pady=20, sticky="e")
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=self.COLORS['text_muted']
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        
        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="Ready to start",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_muted']
        )
        self.status_text.pack(side="left")

    def create_main_content(self):
        """Create the main content area with video and controls"""
        content = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.COLORS['bg_dark']
        )
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Left side - Video display
        self.create_video_section(content)
        
        # Right side - Controls and stats
        self.create_sidebar(content)

    def create_video_section(self, parent):
        """Create the video display area"""
        video_container = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS['bg_card'],
            corner_radius=20,
            border_width=1,
            border_color=self.COLORS['border']
        )
        video_container.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=0)
        video_container.grid_columnconfigure(0, weight=1)
        video_container.grid_rowconfigure(0, weight=1)

        # Video frame with placeholder
        self.video_frame = ctk.CTkFrame(
            video_container,
            fg_color="#000000",
            corner_radius=15
        )
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.video_frame.grid_columnconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(0, weight=1)

        # Placeholder content
        self.placeholder_frame = ctk.CTkFrame(self.video_frame, fg_color="transparent")
        self.placeholder_frame.grid(row=0, column=0)
        
        placeholder_icon = ctk.CTkLabel(
            self.placeholder_frame,
            text="📹",
            font=ctk.CTkFont(size=60)
        )
        placeholder_icon.pack(pady=(0, 15))
        
        placeholder_text = ctk.CTkLabel(
            self.placeholder_frame,
            text="Click 'Start Camera' to begin tracking",
            font=ctk.CTkFont(size=16),
            text_color=self.COLORS['text_muted']
        )
        placeholder_text.pack()

        # Video label (hidden initially)
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        
    def create_sidebar(self, parent):
        """Create the sidebar with controls and statistics"""
        sidebar = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS['bg_card'],
            corner_radius=20,
            border_width=1,
            border_color=self.COLORS['border'],
            width=320
        )
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_propagate(False)

        # Controls Section
        self.create_controls_section(sidebar)
        
        # Detected Gesture Section
        self.create_gesture_display(sidebar)
        
        # Statistics Section
        self.create_stats_section(sidebar)
        
        # Gesture History Section
        self.create_history_section(sidebar)

    def create_controls_section(self, parent):
        """Create camera control buttons"""
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=20)

        section_title = ctk.CTkLabel(
            controls_frame,
            text="CONTROLS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLORS['text_muted']
        )
        section_title.pack(anchor="w", pady=(0, 15))

        # Webcam button
        self.webcam_button = ctk.CTkButton(
            controls_frame,
            text="▶  Start Camera",
            command=self.toggle_webcam,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=self.COLORS['primary'],
            hover_color=self.COLORS['primary_hover']
        )
        self.webcam_button.pack(fill="x", pady=(0, 10))

        # Upload button
        self.upload_button = ctk.CTkButton(
            controls_frame,
            text="📁  Upload Video",
            command=self.upload_file,
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=12,
            fg_color=self.COLORS['bg_card_hover'],
            hover_color=self.COLORS['border'],
            border_width=1,
            border_color=self.COLORS['border']
        )
        self.upload_button.pack(fill="x")

        # File name label
        self.file_label = ctk.CTkLabel(
            controls_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_muted']
        )
        self.file_label.pack(pady=(5, 0))

    def create_gesture_display(self, parent):
        """Create the current gesture display card"""
        gesture_frame = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS['bg_card_hover'],
            corner_radius=15
        )
        gesture_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Header
        header = ctk.CTkFrame(gesture_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        section_title = ctk.CTkLabel(
            header,
            text="DETECTED GESTURE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLORS['text_muted']
        )
        section_title.pack(anchor="w")

        # Gesture emoji and name
        self.gesture_emoji = ctk.CTkLabel(
            gesture_frame,
            text="🖐️",
            font=ctk.CTkFont(size=50)
        )
        self.gesture_emoji.pack(pady=(10, 5))

        self.gesture_name = ctk.CTkLabel(
            gesture_frame,
            text="Waiting...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.COLORS['text']
        )
        self.gesture_name.pack(pady=(0, 5))

        self.gesture_confidence = ctk.CTkLabel(
            gesture_frame,
            text="Confidence: --",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_muted']
        )
        self.gesture_confidence.pack(pady=(0, 15))

    def create_stats_section(self, parent):
        """Create statistics display"""
        stats_frame = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS['bg_card_hover'],
            corner_radius=15
        )
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))

        section_title = ctk.CTkLabel(
            stats_frame,
            text="SESSION STATS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLORS['text_muted']
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Stats grid
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=(0, 15))
        stats_grid.grid_columnconfigure((0, 1), weight=1)

        # Gestures Count
        self.create_stat_item(stats_grid, "Gestures", "0", 0, 0, self.COLORS['primary'])
        
        # Session Time
        self.create_stat_item(stats_grid, "Duration", "00:00", 0, 1, self.COLORS['secondary'])

    def create_stat_item(self, parent, label, value, row, col, color):
        """Create a single stat display item"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color
        )
        value_label.pack()
        
        if label == "Gestures":
            self.gestures_count_label = value_label
        elif label == "Duration":
            self.duration_label = value_label

        title_label = ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_muted']
        )
        title_label.pack()

    def create_history_section(self, parent):
        """Create gesture history log"""
        history_frame = ctk.CTkFrame(parent, fg_color="transparent")
        history_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        section_title = ctk.CTkLabel(
            history_frame,
            text="GESTURE LOG",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLORS['text_muted']
        )
        section_title.pack(anchor="w", pady=(0, 10))

        # Scrollable history
        self.history_list = ctk.CTkScrollableFrame(
            history_frame,
            fg_color=self.COLORS['bg_card_hover'],
            corner_radius=10,
            height=150
        )
        self.history_list.pack(fill="both", expand=True)
        
        # Placeholder text
        self.history_placeholder = ctk.CTkLabel(
            self.history_list,
            text="No gestures detected yet",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_muted']
        )
        self.history_placeholder.pack(pady=20)

    def create_footer(self):
        """Create the footer"""
        footer = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.COLORS['bg_card'],
            corner_radius=0,
            height=50
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        # Left side - Supported gestures
        gestures_label = ctk.CTkLabel(
            footer,
            text="✋👍👎✌️👌🤘🤙🤟☝️👊🤏🖖 + more gestures supported!",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_muted']
        )
        gestures_label.grid(row=0, column=0, padx=30, pady=15, sticky="w")

        # Right side - Version
        version_label = ctk.CTkLabel(
            footer,
            text="v2.1.0  •  Powered by MediaPipe",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_muted']
        )
        version_label.grid(row=0, column=2, padx=30, pady=15, sticky="e")

    def update_status(self, text: str, status: str = "default"):
        """Update status indicator"""
        colors = {
            "active": self.COLORS['success'],
            "error": self.COLORS['danger'],
            "warning": self.COLORS['warning'],
            "default": self.COLORS['text_muted']
        }
        color = colors.get(status, colors['default'])
        self.status_dot.configure(text_color=color)
        self.status_text.configure(text=text, text_color=color)

    def toggle_webcam(self):
        """Toggle webcam on/off"""
        if not self.is_webcam_active:
            self.webcam_button.configure(
                text="⏹  Stop Camera",
                fg_color=self.COLORS['danger'],
                hover_color="#dc2626"
            )
            self.update_status("Camera active", "active")
            self.is_webcam_active = True
            self.session_start_time = time.time()
            
            # Hide placeholder, show video
            self.placeholder_frame.grid_forget()
            self.video_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            # Start webcam thread
            self.video_thread = threading.Thread(target=self.process_webcam, daemon=True)
            self.video_thread.start()
        else:
            self.webcam_button.configure(
                text="▶  Start Camera",
                fg_color=self.COLORS['primary'],
                hover_color=self.COLORS['primary_hover']
            )
            self.update_status("Camera stopped", "default")
            self.is_webcam_active = False

            if self.cap:
                self.cap.release()
            
            # Show placeholder
            self.video_label.grid_forget()
            self.placeholder_frame.grid(row=0, column=0)

    def upload_file(self):
        """Handle file upload"""
        file_types = (("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*"))
        file_path = ctk.filedialog.askopenfilename(filetypes=file_types)
        
        if file_path:
            filename = os.path.basename(file_path)
            self.file_label.configure(text=f"📎 {filename}")
            self.update_status("Processing video...", "warning")
            
            if self.is_webcam_active:
                self.toggle_webcam()

            # Hide placeholder
            self.placeholder_frame.grid_forget()
            self.video_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            
            self.session_start_time = time.time()
            self.video_thread = threading.Thread(
                target=self.process_video,
                args=(file_path,),
                daemon=True
            )
            self.video_thread.start()

    def process_webcam(self):
        """Process webcam feed"""
        try:
            # Try DSHOW backend first on Windows
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                self.window.after(0, lambda: self.update_status("Could not open webcam", "error"))
                self.is_webcam_active = False
                self.window.after(0, lambda: self.webcam_button.configure(
                    text="▶  Start Camera",
                    fg_color=self.COLORS['primary']
                ))
                return

            self.window.after(0, lambda: self.update_status("Initializing tracker...", "warning"))
            self.tracker = HandTracker()
            self.window.after(0, lambda: self.update_status("Tracking active", "active"))
            
            while self.is_webcam_active:
                success, frame = self.cap.read()
                if not success:
                    break

                processed_frame = self.tracker.process_frame(frame)
                
                # Try to add to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(processed_frame)
                except queue.Full:
                    pass

            self.cap.release()
            if self.tracker:
                self.tracker.close()
                
        except Exception as e:
            error_msg = str(e)
            self.window.after(0, lambda: self.update_status(f"Error: {error_msg[:50]}", "error"))
            self.is_webcam_active = False
            if self.cap:
                self.cap.release()

    def process_video(self, file_path: str):
        """Process uploaded video file"""
        try:
            self.cap = cv2.VideoCapture(file_path)
            self.tracker = HandTracker()
            
            while self.cap.isOpened():
                success, frame = self.cap.read()
                if not success:
                    break

                processed_frame = self.tracker.process_frame(frame)
                
                try:
                    self.frame_queue.put_nowait(processed_frame)
                except queue.Full:
                    pass

                # Control playback speed
                time.sleep(0.03)

            self.cap.release()
            self.tracker.close()
            self.window.after(0, lambda: self.update_status("Video completed", "default"))
            self.window.after(0, lambda: self.file_label.configure(text=""))
            
        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"Error: {str(e)[:50]}", "error"))

    def update_video_loop(self):
        """Update video display from queue"""
        try:
            while not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                
                # Resize frame to fit display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Calculate display size maintaining aspect ratio
                display_height = 500
                h, w = frame.shape[:2]
                aspect = w / h
                display_width = int(display_height * aspect)
                
                frame = cv2.resize(frame, (display_width, display_height))
                
                image = PIL.Image.fromarray(frame)
                photo = PIL.ImageTk.PhotoImage(image=image)
                
                self.video_label.configure(image=photo)
                self.video_label.image = photo
                
        except queue.Empty:
            pass
        
        self.window.after(15, self.update_video_loop)

    def update_stats_loop(self):
        """Update statistics display"""
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.duration_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        
        self.window.after(1000, self.update_stats_loop)

    def add_gesture_to_history(self, gesture_name: str, confidence: float):
        """Add a detected gesture to the history log"""
        if hasattr(self, 'history_placeholder') and self.history_placeholder.winfo_exists():
            self.history_placeholder.destroy()
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        entry = ctk.CTkFrame(self.history_list, fg_color="transparent", height=30)
        entry.pack(fill="x", pady=2)
        
        time_label = ctk.CTkLabel(
            entry,
            text=timestamp,
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_muted'],
            width=60
        )
        time_label.pack(side="left", padx=(10, 5))
        
        gesture_label = ctk.CTkLabel(
            entry,
            text=gesture_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLORS['text']
        )
        gesture_label.pack(side="left")
        
        # Keep only last 20 entries
        children = self.history_list.winfo_children()
        if len(children) > 20:
            children[0].destroy()

    def run(self):
        """Start the application"""
        self.window.mainloop()


if __name__ == "__main__":
    app = ModernHandTrackerUI()
    app.run()