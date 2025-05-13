// Import types only for TypeScript compilation
import type { MediaRecorder } from "extendable-media-recorder";

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
let initializationPromise: Promise<void> | null = null;

// Check if we're in the browser environment
const isBrowser = typeof window !== "undefined";

/**
 * WAV Recorder utility for recording audio in WAV format
 */
export class WavRecorder {
  private mediaRecorder: ExtendableMediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private destinationStream: MediaStream | null = null;
  private static initialized = false;

  /**
   * Initialize the WAV encoder
   * This must be called before any recording can happen
   * This method is safe to call multiple times from different components
   */
  static async initialize(): Promise<void> {
    // If we're not in a browser, return immediately
    if (!isBrowser) {
      return Promise.resolve();
    }

    // If already initializing, return the existing promise
    if (initializationPromise) {
      return initializationPromise;
    }

    // Use global flag to prevent multiple initialization across module reloads
    if (!globalInitialized) {
      initializationPromise = (async () => {
        try {
          console.log("Initializing WAV encoder...");

          // Dynamically import the modules only in browser environment
          const { register } = await import("extendable-media-recorder");
          const { connect } = await import(
            "extendable-media-recorder-wav-encoder"
          );

          // First attempt to connect to the encoder
          const encoderConnection = await connect();

          // Then attempt to register it
          await register(encoderConnection);

          // Set flags after successful initialization
          globalInitialized = true;
          WavRecorder.initialized = true;
          console.log("WAV encoder initialized successfully");
        } catch (error: any) {
          // Handle the specific error about encoder already being registered
          if (
            error &&
            error.message &&
            error.message.includes("already an encoder stored")
          ) {
            console.log("WAV encoder already registered, continuing...");
            // This is actually a success case, so we set the initialized flags
            globalInitialized = true;
            WavRecorder.initialized = true;
          } else {
            // For other errors, reset flags and rethrow
            console.error("Failed to initialize WAV encoder:", error);
            throw error;
          }
        }
      })();

      try {
        await initializationPromise;
        return initializationPromise;
      } catch (error) {
        // Reset initialization state on error
        globalInitialized = false;
        WavRecorder.initialized = false;
        initializationPromise = null;
        console.error("Fatal error initializing WAV encoder:", error);
        throw error;
      }
    } else {
      // Already initialized globally, just ensure class flag is set
      WavRecorder.initialized = true;
      console.log("WAV encoder already initialized, skipping...");
      return Promise.resolve();
    }
  }

  /**
   * Start recording audio in WAV format
   * @returns Promise that resolves when recording has started
   */
  async startRecording(): Promise<void> {
    // Check if we're in a browser environment
    if (!isBrowser) {
      return Promise.reject(
        new Error("Recording is only available in browser environments"),
      );
    }

    // Make sure WAV encoder is initialized
    if (!WavRecorder.initialized) {
      await WavRecorder.initialize();
    }

    this.audioChunks = [];

    try {
      // Create an AudioContext to control sample rate for better compatibility
      this.audioContext = new AudioContext({
        sampleRate: 16000, // Use a common sample rate for speech recognition
      });

      // Get user media with audio
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Set up audio nodes for proper sample rate conversion
      const source = this.audioContext.createMediaStreamSource(this.stream);
      const destination = this.audioContext.createMediaStreamDestination();
      source.connect(destination);

      // Store the destination stream for recording
      this.destinationStream = destination.stream;

      // Dynamically import MediaRecorder to avoid SSR issues
      const { MediaRecorder } = await import("extendable-media-recorder");

      // Create MediaRecorder with WAV format and explicitly cast to ExtendableMediaRecorder
      this.mediaRecorder = new MediaRecorder(this.destinationStream, {
        mimeType: "audio/wav",
      }) as ExtendableMediaRecorder;

      // Use ondataavailable instead of addEventListener to avoid type issues
      this.mediaRecorder.ondataavailable = (event: any) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(); // The timeslice is now set in the constructor

      if (this.mediaRecorder) {
        console.log(
          "WAV recording started with MIME type:",
          this.mediaRecorder.mimeType,
          "at sample rate:",
          this.audioContext.sampleRate,
        );
      }
    } catch (error) {
      // Clean up resources on error
      this.closeResources();
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
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        reject(new Error("No recording in progress"));
        return;
      }

      // Request final data from the recorder if the method exists
      if (this.mediaRecorder.state === "recording") {
        // Check if requestData method exists before calling it
        if (typeof this.mediaRecorder.requestData === "function") {
          this.mediaRecorder.requestData();
        } else {
          console.warn(
            "MediaRecorder.requestData is not available - this is expected on some browsers",
          );
        }
      }

      // Use onstop instead of addEventListener to avoid type issues
      this.mediaRecorder.onstop = () => {
        // Create WAV blob with explicit mime type
        const mimeType = this.mediaRecorder?.mimeType || "audio/wav";

        // Check if we have any chunks before creating blob
        if (this.audioChunks.length === 0) {
          this.closeResources();
          reject(new Error("No audio data recorded"));
          return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: mimeType });

        // Log detailed info for debugging
        console.log("WAV recording stopped, details:", {
          size: audioBlob.size,
          chunks: this.audioChunks.length,
          mimeType: audioBlob.type,
        });

        // Clean up resources
        this.closeResources();

        if (audioBlob.size > 0) {
          resolve(audioBlob);
        } else {
          reject(new Error("Recorded audio has zero size"));
        }
      };

      // Safe access to mediaRecorder
      if (this.mediaRecorder) {
        try {
          this.mediaRecorder.stop();
        } catch (error) {
          this.closeResources();
          reject(error);
        }
      } else {
        this.closeResources();
        reject(new Error("MediaRecorder is not active"));
      }
    });
  }

  /**
   * Close and clean up all resources
   */
  private closeResources(): void {
    // Stop all tracks in the original stream
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    // Stop all tracks in the destination stream
    if (this.destinationStream) {
      this.destinationStream.getTracks().forEach((track) => track.stop());
      this.destinationStream = null;
    }

    // Close AudioContext
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close().catch(console.error);
      this.audioContext = null;
    }

    // Clear audio chunks
    this.audioChunks = [];

    // Clear media recorder
    this.mediaRecorder = null;
  }
}

export default WavRecorder;
