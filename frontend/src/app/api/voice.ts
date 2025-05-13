import { API_BASE_URL } from "@/app/config/api";

// Types
export interface VoiceResponse {
  id: string;
}

export interface TextToSpeechRequest {
  text: string;
  voice_id?: string;
  speaker_id?: number;
}

export interface TranscriptionResponse {
  text: string;
  segments: any[];
  vtt?: string;
  srt?: string;
  language: string;
}

// TTS Functions
export async function listVoices(): Promise<VoiceResponse[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tts/voices`);
    if (!response.ok) {
      throw new Error(`Failed to list voices: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error listing voices:", error);
    throw error;
  }
}

export async function synthesizeSpeech(
  request: TextToSpeechRequest,
): Promise<ArrayBuffer> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tts/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to synthesize speech: ${response.status}`);
    }

    return await response.arrayBuffer();
  } catch (error) {
    console.error("Error synthesizing speech:", error);
    throw error;
  }
}

// STT Functions
export async function transcribeAudio(
  audioData: Blob,
  language: string = "en",
  format: string = "webm",
): Promise<TranscriptionResponse> {
  try {
    // Make sure format is valid
    const validFormats = ["webm", "mp4", "wav", "ogg"];
    const validFormat = validFormats.includes(format) ? format : "webm";

    // Create a properly named file with the correct extension to help the server
    // recognize the format correctly
    const fileName = `recording.${validFormat}`;

    // For WAV files, use the proper MIME type
    const mimeType =
      validFormat === "wav" ? "audio/wav" : `audio/${validFormat}`;

    const file = new File([audioData], fileName, {
      type: mimeType,
    });

    console.log(
      `Preparing file for transcription: ${fileName} with type: ${mimeType}`,
    );

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("format", validFormat);

    const response = await fetch(`${API_BASE_URL}/api/stt/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to transcribe audio: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error transcribing audio:", error);
    throw error;
  }
}

export async function transcribeAudioBuffer(
  audioBuffer: ArrayBuffer,
  language: string = "en",
  translate: boolean = false,
  format: string = "wav",
): Promise<TranscriptionResponse> {
  try {
    const url = `${API_BASE_URL}/api/stt/transcribe/buffer?language=${language}&translate=${translate}&format=${format}`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/octet-stream",
      },
      body: audioBuffer,
    });

    if (!response.ok) {
      throw new Error(`Failed to transcribe audio buffer: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error transcribing audio buffer:", error);
    throw error;
  }
}
