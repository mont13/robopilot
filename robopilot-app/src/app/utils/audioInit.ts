/**
 * This file handles initialization of audio-related features
 */
import WavRecorder from "./wavRecorder";

/**
 * Initialize all audio-related functionality that needs to be done
 * at application start time
 */
export async function initializeAudio() {
  try {
    console.log("Initializing audio subsystems...");

    // Initialize WAV encoder for high-quality recording
    await WavRecorder.initialize();

    console.log("Audio initialization complete");
    return true;
  } catch (error) {
    console.error("Failed to initialize audio systems:", error);
    return false;
  }
}

export default initializeAudio;
