import React, { useState, useEffect } from "react";
import WavRecorder from "@/app/utils/wavRecorder";

/**
 * Simple component for testing WAV recording functionality
 */
export default function AudioTester() {
  const [recorder, setRecorder] = useState<WavRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Initialize WAV recorder
  useEffect(() => {
    const initRecorder = async () => {
      try {
        // Don't initialize here - it's already done at app startup
        // Just create a new recorder instance
        setRecorder(new WavRecorder());
        setInitialized(true);
      } catch (error) {
        console.error("Failed to initialize audio recorder:", error);
      }
    };

    initRecorder();

    // Cleanup
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);

  const startRecording = async () => {
    if (!recorder) return;

    try {
      await recorder.startRecording();
      setIsRecording(true);
      setAudioUrl(null);
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  };

  const stopRecording = async () => {
    if (!recorder || !isRecording) return;

    try {
      const audioBlob = await recorder.stopRecording();
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      setIsRecording(false);

      console.log("Audio recorded successfully:", {
        format: "wav",
        size: audioBlob.size,
        type: audioBlob.type,
      });
    } catch (error) {
      console.error("Failed to stop recording:", error);
      setIsRecording(false);
    }
  };

  if (!initialized) {
    return <div>Initializing audio recorder...</div>;
  }

  return (
    <div
      style={{ padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}
    >
      <h2>Audio WAV Test</h2>

      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={isRecording ? stopRecording : startRecording}
          style={{
            padding: "10px 20px",
            backgroundColor: isRecording ? "red" : "green",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
      </div>

      {audioUrl && (
        <div>
          <h3>Recorded Audio (WAV)</h3>
          <audio controls src={audioUrl} />
        </div>
      )}
    </div>
  );
}
