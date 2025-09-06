import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface SettingsState {
  // Audio settings
  selectedVoice: string | null;
  speakerId: number;
  transcriptionLanguage: string;
  isAudioEnabled: boolean;
  vadEnabled: boolean;

  // UI settings
  isMobile: boolean;

  // Interaction mode
  interactionMode: "chat" | "voice" | null;

  // TTS settings
  ttsEnabled: boolean;
  ttsAutoPlay: boolean;

  // Streaming settings
  streamingEnabled: boolean;
}

const initialState: SettingsState = {
  // Audio settings
  selectedVoice: null,
  speakerId: 0,
  transcriptionLanguage: "en",
  isAudioEnabled: true,
  vadEnabled: true,

  // UI settings
  isMobile: false,

  // Interaction mode
  interactionMode: null,

  // TTS settings
  ttsEnabled: true,
  ttsAutoPlay: true,

  // Streaming settings
  streamingEnabled: false,
};

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    // Audio settings
    setSelectedVoice: (state, action: PayloadAction<string | null>) => {
      state.selectedVoice = action.payload;
    },
    setSpeakerId: (state, action: PayloadAction<number>) => {
      state.speakerId = action.payload;
    },
    setTranscriptionLanguage: (state, action: PayloadAction<string>) => {
      state.transcriptionLanguage = action.payload;
    },
    setIsAudioEnabled: (state, action: PayloadAction<boolean>) => {
      state.isAudioEnabled = action.payload;
    },
    setVadEnabled: (state, action: PayloadAction<boolean>) => {
      state.vadEnabled = action.payload;
    },

    // UI settings
    setIsMobile: (state, action: PayloadAction<boolean>) => {
      state.isMobile = action.payload;
    },

    // Interaction mode
    setInteractionMode: (
      state,
      action: PayloadAction<"chat" | "voice" | null>,
    ) => {
      state.interactionMode = action.payload;
    },

    // TTS settings
    setTtsEnabled: (state, action: PayloadAction<boolean>) => {
      state.ttsEnabled = action.payload;
    },
    setTtsAutoPlay: (state, action: PayloadAction<boolean>) => {
      state.ttsAutoPlay = action.payload;
    },

    // Streaming settings
    setStreamingEnabled: (state, action: PayloadAction<boolean>) => {
      state.streamingEnabled = action.payload;
    },

    // Bulk settings update
    updateSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      return { ...state, ...action.payload };
    },

    // Reset settings
    resetSettings: () => initialState,
  },
});

export const {
  setSelectedVoice,
  setSpeakerId,
  setTranscriptionLanguage,
  setIsAudioEnabled,
  setVadEnabled,
  setIsMobile,
  setInteractionMode,
  setTtsEnabled,
  setTtsAutoPlay,
  setStreamingEnabled,
  updateSettings,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;

// Selectors
export const selectSettings = (state: any) => state.settings;
export const selectAudioSettings = (state: any) => ({
  selectedVoice: state.settings?.selectedVoice,
  speakerId: state.settings?.speakerId,
  transcriptionLanguage: state.settings?.transcriptionLanguage,
  isAudioEnabled: state.settings?.isAudioEnabled,
  vadEnabled: state.settings?.vadEnabled,
});
export const selectTtsSettings = (state: any) => ({
  ttsEnabled: state.settings?.ttsEnabled,
  ttsAutoPlay: state.settings?.ttsAutoPlay,
});
export const selectStreamingSettings = (state: any) => ({
  streamingEnabled: state.settings?.streamingEnabled,
});
export const selectInteractionMode = (state: any) =>
  state.settings?.interactionMode;
