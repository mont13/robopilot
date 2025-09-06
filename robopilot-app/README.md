# RoboPilot Mobile App

A React Native mobile application built with Expo SDK v54 that provides a conversational AI interface with both text and voice input capabilities.

## Features

### Core Functionality
- **Chat Interface**: Clean, scrollable message history with user and assistant messages
- **Session Management**: Create new chat sessions and persist conversation history
- **Dual Input Modes**: Switch between keyboard and voice input with a single tap
- **Text-to-Speech**: Automatic TTS playback for assistant responses in voice mode
- **Voice Recognition**: Uses expo-speech-recognition and react-native-wakeword for voice input
- **Offline Support**: Local message persistence with AsyncStorage

### Technical Features
- **Expo SDK v54**: Latest Expo framework with TypeScript support
- **Voice Activity Detection**: Intelligent voice input detection
- **Haptic Feedback**: Enhanced user experience with tactile feedback
- **Connection Status**: Real-time server connection monitoring
- **Error Handling**: Graceful error handling with user-friendly alerts
- **Responsive Design**: Optimized for both iOS and Android devices

## Prerequisites

- Node.js 18.x or higher
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator (macOS) or Android Studio (for Android development)
- Physical device for testing voice features

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd robopilot-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` to set your API base URL:
   ```
   EXPO_PUBLIC_API_BASE_URL=http://your-server:8009
   EXPO_PUBLIC_DEBUG=true
   ```

4. **Start the development server:**
   ```bash
   npm start
   ```

## Running the App

### Development
```bash
# Start Expo development server
npm run dev

# Run on iOS simulator
npm run ios

# Run on Android emulator/device
npm run android

# Run on web (limited functionality)
npm run web
```

### Production Build
```bash
# Build for iOS
expo build:ios

# Build for Android
expo build:android
```

## API Integration

The app connects to your RoboPilot backend server and expects the following endpoints:

### Session Management
- `POST /api/agent/sessions` - Create new session
- `GET /api/agent/sessions/active` - Get active session
- `GET /api/agent/sessions/{id}` - Get session history
- `DELETE /api/agent/sessions/{id}` - Delete session

### Chat
- `POST /api/agent/chat` - Send message (AgentExecutionRequest)

### Voice Services
- `POST /api/stt/transcribe` - Audio transcription
- `POST /api/tts/synthesize` - Text-to-speech synthesis

### Health Check
- `GET /api/health` - Server health status

## Configuration

### Environment Variables
- `EXPO_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8009)
- `EXPO_PUBLIC_DEBUG` - Enable debug logging (default: true)

### Voice Input Setup
The app uses two approaches for voice input:

1. **Primary**: expo-speech-recognition (more accurate)
2. **Fallback**: Audio recording with server-side transcription

### Permissions Required
- **Microphone**: For voice input and recording
- **Speech Recognition**: For native speech-to-text (iOS)

## Architecture

### Core Components
- `app/index.tsx` - Main chat screen
- `components/InputBar.tsx` - Input handling (keyboard/voice toggle)
- `components/MessageBubble.tsx` - Individual message display
- `services/api.ts` - API service layer
- `hooks/useVoiceInput.ts` - Voice input management
- `types/api.ts` - TypeScript type definitions

### State Management
- Local React state for UI interactions
- AsyncStorage for message persistence
- No external state management library (keeps it simple)

### Voice Input Flow
1. User taps voice button or switches to voice mode
2. App requests microphone permissions
3. Attempts native speech recognition (expo-speech-recognition)
4. Falls back to audio recording if native unavailable
5. Transcribes audio via backend API
6. Sends transcribed text as regular message

## Customization

### Styling
All styles are defined in component files using React Native StyleSheet. Key style configurations:

- Colors: Follows a blue/gray theme
- Typography: System fonts with accessible sizing
- Spacing: Consistent 8px grid system
- Shadows: Platform-specific shadow styles

### Voice Settings
Configure voice input in `hooks/useVoiceInput.ts`:
- Language: Default "en-US"
- Timeout: 10 seconds
- Audio quality: 16kHz, 16-bit

### API Timeout
Default API timeout is 30 seconds. Modify in `services/api.ts`.

## Troubleshooting

### Common Issues

1. **Voice input not working**
   - Ensure microphone permissions are granted
   - Check device compatibility with expo-speech-recognition
   - Verify backend transcription service is running

2. **Connection errors**
   - Verify API_BASE_URL in .env file
   - Ensure backend server is running
   - Check network connectivity

3. **Audio playback issues**
   - Test TTS service independently
   - Check device audio settings
   - Verify expo-speech dependencies

### Debugging
- Enable debug mode: `EXPO_PUBLIC_DEBUG=true`
- Use Expo debugging tools: `npx expo install expo-dev-client`
- Check console logs in development

## Development Workflow

### Code Structure
```
robopilot-app/
├── app/                 # Main app screens
├── components/          # Reusable components
├── hooks/              # Custom React hooks
├── services/           # API and external services
├── types/              # TypeScript definitions
└── assets/             # Images and static files
```

### Adding New Features
1. Create components in `components/`
2. Add API methods to `services/api.ts`
3. Update TypeScript types in `types/api.ts`
4. Test on both iOS and Android

### Voice Feature Development
- Test with real devices (simulators have limited audio)
- Handle permission edge cases
- Provide fallback options for unsupported devices

## Deployment

### App Store (iOS)
1. Configure `app.json` with bundle identifier
2. Set up Apple Developer account
3. Build with `expo build:ios`
4. Submit via Xcode or Application Loader

### Google Play (Android)
1. Configure `app.json` with package name
2. Set up Google Play Console account
3. Build with `expo build:android`
4. Upload AAB file to Play Console

### Over-the-Air Updates
Expo supports OTA updates for JavaScript changes:
```bash
expo publish
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review Expo documentation: https://docs.expo.dev/
- Open an issue in the repository

## Acknowledgments

- Built with Expo SDK v54
- Uses expo-speech-recognition for voice input
- Integrates with react-native-wakeword for VAD
- Inspired by modern chat interfaces