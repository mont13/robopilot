import { MediaRecorder, register } from "extendable-media-recorder";
import { connect } from "extendable-media-recorder-wav-encoder";

// Type for the MediaRecorder from extendable-media-recorder
// to fix TypeScript compatibility issues
interface ExtendableMediaRecorder extends MediaRecorder {
  // Add properties that TypeScript expects but might be missing from the library's types
  audioBitsPerSecond: number;
  videoBitsPerSecond: number;
  stream: MediaStream;
  requestData: () => void;
}

/**
 * Track initialization state globally rather than just within the class
 * to prevent multiple initialization attempts across instances
 */
let globalInitialized = false;

/**
 * WAV Recorder utility for recording audio in WAV format
 */
export class WavRecorder {
  private mediaRecorder: ExtendableMediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private static initialized = false;

  /**
   * Initialize the WAV encoder
   * This must be called before any recording can happen
   * This method is safe to call multiple times from different components
   */
  static async initialize(): Promise<void> {
    // Use global flag to prevent multiple initialization across module reloads
    if (!globalInitialized) {
      try {
        // Set flag first to prevent race conditions with multiple simultaneous calls
        globalInitialized = true;
        WavRecorder.initialized = true;

        try {
          // First attempt to connect to the encoder
          const encoderConnection = await connect();

          // Then attempt to register it
          await register(encoderConnection);
          console.log("WAV encoder initialized successfully");
        } catch (error: any) {
          // Handle the specific error about encoder already being registered
          if (
            error &&
            error.message &&
            error.message.includes("already an encoder stored")
          ) {
            console.log("WAV encoder already registered, continuing...");
            // This is actually a success case, so we keep the initialized flags true
          } else {
            // For other errors, reset flags and rethrow
            globalInitialized = false;
            WavRecorder.initialized = false;
            console.error("Failed to initialize WAV encoder:", error);
            throw error;
          }
        }
      } catch (error) {
        // Final error handler
        globalInitialized = false;
        WavRecorder.initialized = false;
        console.error("Fatal error initializing WAV encoder:", error);
        throw error;
      }
    } else {
      // Already initialized globally, just ensure class flag is set
      WavRecorder.initialized = true;
      console.log("WAV encoder already initialized, skipping...");
    }
  }

  /**
   * Start recording audio in WAV format
   * @returns Promise that resolves when recording has started
   */
  async startRecording(): Promise<void> {
    // Make sure WAV encoder is initialized
    if (!WavRecorder.initialized) {
      await WavRecorder.initialize();
    }

    this.audioChunks = [];

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create MediaRecorder with WAV format and explicitly cast to ExtendableMediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: "audio/wav",
      }) as ExtendableMediaRecorder;

      // Use ondataavailable instead of addEventListener to avoid type issues
      this.mediaRecorder.ondataavailable = (event: any) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(100); // Record in chunks of 100ms

      if (this.mediaRecorder) {
        console.log(
          "WAV recording started with MIME type:",
          this.mediaRecorder.mimeType
        );
      }
    } catch (error) {
      console.error("Error starting WAV recording:", error);
      throw error;
    }
  }

  /**
   * Stop recording and get the WAV audio blob
   * @returns Promise that resolves with the recorded WAV audio blob
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error("No recording in progress"));
        return;
      }

      // Use onstop instead of addEventListener to avoid type issues
      this.mediaRecorder.onstop = () => {
        // Create WAV blob
        const mimeType = this.mediaRecorder?.mimeType || "audio/wav";
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });

        // Stop all tracks
        if (this.stream) {
          this.stream.getTracks().forEach((track) => track.stop());
          this.stream = null;
        }

        console.log("WAV recording stopped, blob size:", audioBlob.size);
        resolve(audioBlob);
      };

      // Safe access to mediaRecorder
      if (this.mediaRecorder) {
        this.mediaRecorder.stop();
      }
    });
  }
}

export default WavRecorder;
