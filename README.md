# Smol Agency - AI Chat Interface

## Overview

Smol Agency is a modern, responsive web application that provides an intuitive chat interface for interacting with AI assistants. The platform supports real-time conversations, file uploads/downloads, and dynamic theme switching, all within a clean and user-friendly interface.

## Features

- **Interactive Chat Interface**: Engage in natural conversations with AI assistants
- **File Management**:
  - Upload files to include in your conversations
  - Download generated files directly from the chat
  - Browse and manage files through the sidebar
- **Real-time Responses**: Stream responses as they're generated for a more natural conversation flow
- **Tool Execution**: Watch as the AI executes tools and displays results in real-time
- **Theme Support**: Toggle between light and dark themes based on your preference
- **Responsive Design**: Works seamlessly across desktop and mobile devices
- **Custom Scrollbars**: Themed scrollbars that adapt to the current color scheme
- **Markdown Support**: Rich text formatting in messages with code highlighting

## Installation

### Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/smol-agency.git
   cd smol-agency
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start the application:
   ```bash
   python app.py
   ```

6. Access the application at `http://localhost:8000`

## Usage

### Starting a Conversation

1. Type your message in the input field at the bottom of the screen
2. Press Enter or click the Send button to submit your message
3. View the AI's response as it streams in real-time

### Uploading Files

1. Click the paperclip icon next to the input field
2. Select one or more files from your device
3. The files will appear in the chat input area
4. Send your message along with the files

### Downloading Files

- Click on any file item in the chat or sidebar to download it
- Files generated by the AI will appear in the chat and in the sidebar for easy access

### Changing Themes

- Click the theme toggle button in the header to switch between light and dark modes

## Configuration

The application can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the server on | 8000 |
| `DEBUG` | Enable debug mode | False |
| `MODEL_NAME` | AI model to use | "gpt-3.5-turbo" |
| `MAX_TOKENS` | Maximum tokens per response | 2048 |
| `TEMPERATURE` | Response randomness (0-1) | 0.7 |

## Project Structure

```
smol-agency/
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── frontend/              # Frontend assets
│   ├── static/
│   │   ├── css/           # Stylesheets
│   │   ├── js/            # JavaScript files
│   │   └── img/           # Images and icons
│   └── templates/         # HTML templates
├── routes/                # API routes
├── services/              # Business logic
└── utils/                 # Utility functions
```

## Technologies Used

### Frontend
- HTML5, CSS3, JavaScript
- Custom CSS variables for theming
- Fetch API for AJAX requests
- Markdown rendering

### Backend
- Python
- FastAPI/Flask (depending on your implementation)
- WebSockets for streaming responses
- File handling utilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Icons provided by [FontAwesome](https://fontawesome.com/)
- Inspired by modern chat interfaces like ChatGPT and Discord
