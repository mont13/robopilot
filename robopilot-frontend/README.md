# LM Studio Agents Demo

This project demonstrates how to build conversational agents using local LLMs with LM Studio.

## Features

- Text-based chat with configurable AI agents 
- Voice input with browser-based speech recognition
- Text-to-speech output with browser's speech synthesis API
- Tool/function calling support for complex tasks
- Multiple agent "scenarios" with different personalities and capabilities

## Prerequisites

- [LM Studio](https://lmstudio.ai/) installed on your computer
- A compatible LLM downloaded in LM Studio (Gemma 3, Llama 3, or others with function calling support)
- Node.js and npm

## Setup Instructions

1. Clone this repository:
   ```
   git clone <repository-url>
   cd openai-realtime-agents
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start LM Studio:
   - Launch LM Studio
   - Load a compatible model (recommended: Gemma 3 or Llama 3)
   - Go to the "Local Server" tab and click "Start Server"
   - The server should be running at `http://localhost:1234`

4. Start the development server:
   ```
   npm run dev
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

## Usage

- Click "Connect" to establish a connection with LM Studio
- Type messages in the text box or use the "Talk" button for voice input
- Switch between different agent scenarios using the dropdown menu
- Toggle logs to see detailed event information

## Implementation Notes

- The project uses LM Studio's OpenAI-compatible API interface
- Voice input is handled through the Web Audio API and a custom transcription service
- Text-to-speech is provided by the browser's built-in Speech Synthesis API
- The UI is built with React and Tailwind CSS

## Known Limitations

- Voice transcription may not work perfectly with all accents and languages
- Function calling support varies between different LLMs
- Some LLMs may produce unexpected results due to differences in training data
- Text-to-speech quality depends on the voices available in your browser/OS

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.