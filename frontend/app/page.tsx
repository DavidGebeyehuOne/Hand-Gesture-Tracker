"use client";

import React, { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import { Hand, Camera, StopCircle, ArrowRight, ShieldCheck, Activity, BrainCircuit } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5000";

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const displayCanvasRef = useRef<HTMLCanvasElement>(null);
  
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Ready");
  
  const captureIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io(BACKEND_URL, {
      transports: ["websocket", "polling"],
    });

    newSocket.on("connect", () => {
      setIsConnected(true);
      setStatusMessage("Connected to Server");
    });

    newSocket.on("disconnect", () => {
      setIsConnected(false);
      setStatusMessage("Disconnected from backend server.");
      stopTracking();
    });

    newSocket.on("frame", (data: { image: string }) => {
      if (displayCanvasRef.current) {
        const ctx = displayCanvasRef.current.getContext("2d");
        const img = new Image();
        img.onload = () => {
          if (displayCanvasRef.current) {
             ctx?.clearRect(0, 0, displayCanvasRef.current.width, displayCanvasRef.current.height);
             ctx?.drawImage(img, 0, 0, displayCanvasRef.current.width, displayCanvasRef.current.height);
          }
        };
        img.src = data.image;
      }
    });

    setSocket(newSocket);
    return () => {
      newSocket.close();
    };
  }, []);

  const startTracking = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Local webcam not supported in this browser");
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480, facingMode: "user" } 
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      setIsTracking(true);
      setStatusMessage("Tracking Active");

      // Set up frame capture and transmission
      captureIntervalRef.current = setInterval(() => {
        captureAndSendFrame();
      }, 100); // 10 FPS
      
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Camera Error: ${err.message}`);
    }
  };

  const captureAndSendFrame = () => {
    if (!videoRef.current || !canvasRef.current || !socket || !isConnected) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Ensure canvas dimensions match video
    if (canvas.width !== videoRef.current.videoWidth) {
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
    }
    
    if (displayCanvasRef.current && displayCanvasRef.current.width !== videoRef.current.videoWidth) {
        displayCanvasRef.current.width = videoRef.current.videoWidth;
        displayCanvasRef.current.height = videoRef.current.videoHeight;
    }

    // Draw current video frame to canvas
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Get Base64 image
    const dataUrl = canvas.toDataURL("image/jpeg", 0.7);

    // Send to backend
    socket.emit("frame", dataUrl);
  };

  const stopTracking = () => {
    setIsTracking(false);
    setStatusMessage(isConnected ? "Ready" : "Disconnected");

    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }

    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    // Clear display canvas
    if (displayCanvasRef.current) {
      const ctx = displayCanvasRef.current.getContext("2d");
      ctx?.clearRect(0, 0, displayCanvasRef.current.width, displayCanvasRef.current.height);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-indigo-500/30 overflow-hidden font-sans">
      {/* Dynamic Background Effects */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-600/10 blur-[120px]" />
      </div>

      <main className="relative z-10 flex flex-col items-center min-h-screen max-w-7xl mx-auto px-6 py-12">
        {/* Header Section */}
        <header className="w-full flex justify-between items-center mb-16">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
              <Hand className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">NEXUS<span className="text-indigo-400">VISION</span></h1>
              <p className="text-xs text-zinc-400 font-medium">Real-Time Hand Tracking</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${isConnected ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
              <span className="text-sm font-semibold tracking-wide uppercase">
                {isConnected ? 'Server Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Presentation Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 w-full">
          
          {/* Main Video Display */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="relative aspect-video w-full rounded-3xl overflow-hidden bg-zinc-900/50 border border-zinc-800/50 backdrop-blur-xl shadow-2xl flex items-center justify-center group">
              {/* Hidden Original Video & Canvas */}
              <video 
                ref={videoRef} 
                className="hidden" 
                playsInline 
                muted 
              />
              <canvas 
                ref={canvasRef} 
                className="hidden" 
              />

              {/* Display Canvas (Annotated from backend) */}
              <canvas
                ref={displayCanvasRef}
                className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${isTracking ? 'opacity-100' : 'opacity-0'}`}
              />

              {/* Placeholder Content */}
              {!isTracking && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900/80 backdrop-blur-sm transition-opacity">
                  <div className="w-20 h-20 mb-6 rounded-2xl bg-zinc-800/50 flex items-center justify-center border border-zinc-700/50 shadow-inner group-hover:scale-105 transition-transform duration-500">
                    <Camera className="w-10 h-10 text-zinc-400" />
                  </div>
                  <h3 className="text-xl font-medium text-zinc-200 mb-2">Camera Inactive</h3>
                  <p className="text-zinc-500 max-w-sm text-center">Start the tracking session to initialize the MediaPipe ML pipeline and connect to the processing server.</p>
                </div>
              )}
              
              {/* Scanning Overlay Effect */}
              {isTracking && (
                <div className="absolute inset-0 pointer-events-none border-2 border-indigo-500/30 rounded-3xl">
                   <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-b from-indigo-500/20 to-transparent animate-[scan_3s_ease-in-out_infinite]" />
                </div>
              )}
            </div>
          </div>

          {/* Control Panel */}
          <div className="lg:col-span-4 flex flex-col gap-6 w-full">
            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-6 backdrop-blur-xl">
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">Operations</h3>
              
              <div className="flex flex-col gap-4">
                {isTracking ? (
                  <button 
                    onClick={stopTracking}
                    className="w-full relative group overflow-hidden bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-all duration-300 rounded-2xl p-4 flex items-center justify-center gap-3 font-semibold tracking-wide"
                  >
                    <StopCircle className="w-5 h-5" />
                    Terminate Feed
                  </button>
                ) : (
                  <button 
                    onClick={startTracking}
                    disabled={!isConnected}
                    className={`w-full relative group overflow-hidden ${!isConnected ? 'opacity-50 cursor-not-allowed bg-zinc-800 text-zinc-500' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)] hover:shadow-[0_0_60px_-15px_rgba(79,70,229,0.7)]'} transition-all duration-300 rounded-2xl p-4 flex items-center justify-center gap-3 font-semibold tracking-wide`}
                  >
                    {isConnected && (
                       <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                    )}
                    <Activity className="w-5 h-5" />
                    Initialize Tracking
                    <ArrowRight className="w-4 h-4 opacity-50 ml-1 group-hover:translate-x-1 transition-transform" />
                  </button>
                )}
              </div>
              
              <div className="mt-6 p-4 rounded-xl bg-black/40 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-zinc-300">System Status</span>
                </div>
                <p className="text-sm text-zinc-500">{statusMessage}</p>
              </div>
            </div>

            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-6 backdrop-blur-xl flex-1 flex flex-col">
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                 <BrainCircuit className="w-4 h-4 text-indigo-400" />
                 Engine Details
              </h3>
              
              <div className="space-y-4 flex-1">
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-sm text-zinc-500">ML Framework</span>
                  <span className="text-sm font-medium text-zinc-300">MediaPipe Tasks API</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-sm text-zinc-500">Connection</span>
                  <span className="text-sm font-medium text-zinc-300">WebSocket / Polling</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-sm text-zinc-500">Latency Profile</span>
                  <span className="text-sm font-medium text-indigo-400">~100ms (Local)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { transform: translateY(0); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; transform: translateY(500px); }
          100% { transform: translateY(500px); opacity: 0; }
        }
      `}} />
    </div>
  );
}
