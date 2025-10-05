# NASA Intergalactic Zoomer 🌌

A high-resolution image zooming application that seamlessly zooms into NASA astronomical images without quality loss. The application uses a backend that serves pre-processed image tiles at different zoom levels, and a frontend that provides smooth interpolation between zoom levels.

## Features

- **Smooth Zooming**: Seamlessly zoom from 1x to 10x with smooth interpolation
- **High Quality**: No quality loss at any zoom level
- **Interactive Controls**: Mouse wheel, keyboard, and button controls for zooming and panning
- **Pre-cached Images**: Backend serves pre-processed images for instant loading
- **Minimum Zoom Lock**: Zoom level is locked at 1x minimum (no zoom out below original size)

## Architecture

### Backend (`photo-zoomer-backend/`)
- **server.py**: Minimalist HTTP server that serves images based on zoom level
- **nasa.py**: Image processing functions (do not modify)
- **interface.py**: Helper functions for image stitching (do not modify)
- **assets/**: Pre-processed image tiles at different zoom levels

### Frontend (`photo-zoomer-frontend/`)
- React-based UI with zoom and pan controls
- Smooth interpolation between integer zoom levels
- Image caching for better performance

## Getting Started

### Prerequisites

**Backend:**
- Python 3.x
- No additional packages needed (uses only stdlib)

**Frontend:**
- Node.js and npm
- React dependencies (installed via npm)

### Running the Application

#### Option 1: Using the startup scripts (recommended)

1. **Start the backend server** (in one terminal):
   ```bash
   ./start-backend.sh
   ```
   The backend will run on http://localhost:8000

2. **Start the frontend** (in another terminal):
   ```bash
   ./start-frontend.sh
   ```
   The frontend will run on http://localhost:3000

#### Option 2: Manual startup

**Backend:**
```bash
cd photo-zoomer-backend
python3 server.py
```

**Frontend:**
```bash
cd photo-zoomer-frontend
npm install  # Only needed first time
npm start
```

## Usage

### Controls

- **Zoom In/Out**: Mouse wheel, or `+`/`-` keys, or sidebar buttons
- **Pan**: Click and drag, or arrow keys
- **Draw Selection**: Ctrl + Click and drag (for future features)
- **Chat**: Enter queries in the sidebar (for future AI integration)

### How It Works

1. The backend serves pre-processed images at different zoom levels (1x, 2x, 3x, etc.)
2. When you zoom, the frontend requests the appropriate zoom level from the backend
3. Between integer zoom levels (e.g., 1.5x), the frontend smoothly interpolates by blending two images
4. Images are cached on the frontend to avoid redundant requests
5. All images are oriented by their top-left corner for consistent positioning

## API Endpoints

### `GET /image`
Returns an image tile for a specific zoom level and position.

**Parameters:**
- `zoom` (int): Zoom level (1, 2, 3, etc.)
- `x` (int): X coordinate (default: 0)
- `y` (int): Y coordinate (default: 0)

**Example:**
```
http://localhost:8000/image?zoom=2&x=0&y=0
```

### `GET /image-info`
Returns information about available zoom levels and coordinates.

**Response:**
```json
{
  "zoom_levels": [1, 2, 3, 4, 5],
  "coordinates": {
    "1": [{"x": 0, "y": 0}],
    "2": [{"x": 0, "y": 0}, {"x": 0, "y": 4300}]
  }
}
```

## Project Structure

```
NASA-IGZOOMERS/
├── photo-zoomer-backend/
│   ├── server.py           # HTTP server endpoint
│   ├── nasa.py             # Image processing (don't modify)
│   ├── interface.py        # Image stitching (don't modify)
│   └── assets/             # Pre-processed image tiles
│       └── test_compression_level_*_x_*_y_*.jpg
├── photo-zoomer-frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── App.css         # Styling
│   │   └── index.js        # Entry point
│   ├── public/
│   └── package.json
├── start-backend.sh        # Backend startup script
├── start-frontend.sh       # Frontend startup script
└── README.md              # This file
```

## Development Notes

- The minimum zoom level is locked at 1x to prevent zooming out beyond the original image size
- Images are fetched on-demand and cached in the frontend
- Smooth transitions are achieved by blending adjacent zoom levels with opacity interpolation
- The backend uses Python's built-in http.server module (no external dependencies)
- CORS is enabled on the backend to allow requests from the React frontend

## Future Enhancements

- Dynamic coordinate calculation based on pan position
- Multi-tile stitching for larger views
- AI-powered feature detection and chat integration
- Export functionality for selected regions
- Support for different image resolutions

## License

NASA data is in the public domain.
