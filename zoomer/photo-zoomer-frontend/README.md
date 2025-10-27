# 🌌 Intergalactic Zoomer

A minimalist React webapp for zooming on large images without quality loss. This frontend provides an intuitive interface for exploring high-resolution images with smooth zooming, square drawing, and chat functionality.

## Features

### 🖼️ Image Navigation
- **Mouse Controls**: Click and drag to pan around the image
- **Keyboard Controls**: Use arrow keys to move around
- **Zoom**: Mouse wheel or +/- keys to zoom in/out
- **Smooth Zooming**: Continuous zoom levels with automatic backend requests at integer steps

### 📦 Square Drawing
- **Interactive Drawing**: Click and drag to draw squares on the image
- **Real-time Preview**: See your square as you draw it
- **Coordinate Tracking**: Automatically logs coordinates for backend requests

### 💬 Chat Interface
- **Query Input**: Send text queries to the backend
- **Real-time Feedback**: Console logging for all backend requests

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```

3. **Open Browser**
   Navigate to `http://localhost:3000`

## Usage

### Navigation
- **Pan**: Click and drag the image or use arrow keys
- **Zoom**: Scroll with mouse wheel or press +/- keys
- **Reset**: Refresh the page to reset position and zoom

### Drawing Squares
1. Click and hold on the image
2. Drag to create a square
3. Release to complete the square
4. Check console for coordinate logging

### Chat
1. Type your query in the chat input
2. Press Enter or click Send
3. Check console for request logging

## Console Logging

The app logs all backend requests to the console:
- 🔄 Zoom level changes (when crossing integer boundaries)
- 📦 Square drawing coordinates
- 💬 Chat messages
- 📡 Backend request details

## Technical Details

- **React 18** with hooks
- **Canvas API** for square drawing
- **CSS Transform** for smooth zooming and panning
- **Event Handling** for keyboard and mouse interactions
- **Responsive Design** for mobile and desktop

## Backend Integration

Currently, the app logs all requests that would be sent to the backend:
- GET requests for new zoom levels
- GET requests with square coordinates
- GET requests with chat queries

Replace the console.log statements with actual API calls when connecting to your backend.

## Customization

- Replace the sample image URL in `App.js` with your actual image
- Modify the zoom range (currently 0.1x to 10x)
- Adjust the pan sensitivity
- Customize the UI colors and styling
