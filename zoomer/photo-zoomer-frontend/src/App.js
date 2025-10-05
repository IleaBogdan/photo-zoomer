
import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';

const BACKEND_URL = 'http://localhost:8000';
const IMAGE_WIDTH = 12200;
const IMAGE_HEIGHT = 8600;
const MAX_INTEGER_ZOOM = 8; // Stop fetching new images beyond this; keep scaling smoothly

function App() {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDrawing, setIsDrawing] = useState(false);
  const [squareStart, setSquareStart] = useState(null);
  const [squareEnd, setSquareEnd] = useState(null);
  const [chatMessage, setChatMessage] = useState('');
  const [lastIntegerZoom, setLastIntegerZoom] = useState(1);
  const [currentImage, setCurrentImage] = useState(null);
  const [imageCache, setImageCache] = useState({});
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [screenStart, setScreenStart] = useState(null);
  const [screenEnd, setScreenEnd] = useState(null);
  
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const offscreenRef = useRef(null);

  // Spectral lines (nm) per element index aligned with symbol list
  const spectralLines = [
    [121.6,102.6,97.3,656.3,486.1,434,410.2],
    [58.4,53.7,51.3,1083,587.6,447.1,501.6,492.2],
    [323.3,670.8,610.4],
    [234.9,313.1,313,455.4,527],
    [69.4,88.3,108.2,136.2,162.3,206.6],
    [777.4,844.6,630,557.7,436.8],
    [95,74.2],
    [585.2,640.2,703.2,724.5,743.9],
    [589,589.6],
    [285.2,279.6],
    [396.2,394.4,669.6],
    [251.6,288.1,390.5],
    [177.5,178.7],
    [180.7,181.2,190],
    [134.7,135.7],
    [696.5,763.5,811.5,842.5,912.3],
  ];
  const elementSymbols = ['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar'];

  // Map average RGB (0-255) to approximate wavelengths (nm)
  const rgbToWavelengths = (r, g, b) => {
    const rw = (800 * (r / 255)) + 700;
    const gw = (300 * (g / 255)) + 400;
    const bw = (400 * (b / 255));
    return [rw, gw, bw];
  };

  const computeElementPresence = (r, g, b) => {
    const [rw, gw, bw] = rgbToWavelengths(r, g, b);
    const tolerances = [10, 10, 10];
    return spectralLines.map((lines) => {
      let score = 0;
      for (let i = 0; i < lines.length; i++) {
        const wl = lines[i];
        if (Math.abs(wl - rw) <= tolerances[0]) score += 1;
        if (Math.abs(wl - gw) <= tolerances[1]) score += 1;
        if (Math.abs(wl - bw) <= tolerances[2]) score += 1;
      }
      return score; // integer score indicating matches
    });
  };

  // Fetch image from backend for a specific zoom level
  const fetchImage = useCallback(async (zoom) => {
    // Calculate coordinates based on zoom level
    const x = Math.round((1 - 1/zoom) * 0.5 * IMAGE_WIDTH);
    const y = Math.round((1 - 1/zoom) * 0.5 * IMAGE_HEIGHT);
    
    const cacheKey = `${zoom}_${x}_${y}`;
    
    // Check cache first
    if (imageCache[cacheKey]) {
      return imageCache[cacheKey];
    }
    
    console.log(`🔄 Fetching image for zoom=${zoom}, x=${x}, y=${y}`);
    
    try {
      const response = await fetch(`${BACKEND_URL}/image?zoom=${zoom}&x=${x}&y=${y}`);
      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Update cache
        setImageCache(prev => ({ ...prev, [cacheKey]: imageUrl }));
        
        return imageUrl;
      } else {
        console.error(`Failed to fetch image for zoom=${zoom}, x=${x}, y=${y}`);
        return null;
      }
    } catch (error) {
      console.error('Error fetching image:', error);
      return null;
    }
  }, [imageCache]);

  // Handle zoom level changes and detect integer steps
  useEffect(() => {
    const currentIntegerZoom = Math.floor(zoomLevel);
    const clampedIntegerZoom = Math.max(1, Math.min(currentIntegerZoom, MAX_INTEGER_ZOOM));
    
    if (clampedIntegerZoom !== lastIntegerZoom) {
      console.log(`🔄 Zoom integer changed: request level ${clampedIntegerZoom} (raw=${currentIntegerZoom})`);
      setLastIntegerZoom(clampedIntegerZoom);
      
      // Fetch only up to MAX_INTEGER_ZOOM; beyond that we keep scaling the last image
      fetchImage(clampedIntegerZoom).then(url => {
        if (url) {
          setCurrentImage(url);
        }
      });
    }
  }, [zoomLevel, lastIntegerZoom, fetchImage]);

  // Initialize with first image
  useEffect(() => {
    fetchImage(1).then(url => {
      if (url) {
        setCurrentImage(url);
      }
    });
  }, [fetchImage]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e) => {
      const step = 0.1;
      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          setPosition(prev => ({ ...prev, y: prev.y - 10 }));
          break;
        case 'ArrowDown':
          e.preventDefault();
          setPosition(prev => ({ ...prev, y: prev.y + 10 }));
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setPosition(prev => ({ ...prev, x: prev.x - 10 }));
          break;
        case 'ArrowRight':
          e.preventDefault();
          setPosition(prev => ({ ...prev, x: prev.x + 10 }));
          break;
        case '+':
        case '=':
          e.preventDefault();
          setZoomLevel(prev => prev + step); // allow zoom beyond 10
          break;
        case '-':
          e.preventDefault();
          setZoomLevel(prev => Math.max(prev - step, 1)); // Don't allow zoom below 1x
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Mouse wheel zoom
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoomLevel(prev => Math.max(1, prev + delta)); // no upper cap, min 1x
  }, []);

  // Mouse drag for panning
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e) => {
    if (e.button === 0 && !e.ctrlKey) { // Left click without Control key
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // square drawing functionality
  const handleCanvasMouseDown = (e) => {
    if (e.button === 0 && e.ctrlKey) { // left click + control key
      const rect = canvasRef.current.getBoundingClientRect();
      const canvas = canvasRef.current;
      
      // Get mouse position relative to the scaled canvas
      const rawX = e.clientX - rect.left;
      const rawY = e.clientY - rect.top;
      
      // Convert from screen coordinates to canvas coordinates
      // The canvas has fixed dimensions but is scaled by CSS, so we need to account for that
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      
      const x = rawX * scaleX;
      const y = rawY * scaleY;

      setIsDrawing(true);
      setSquareStart({ x, y });
      setSquareEnd({ x, y });
      setScreenStart({ x: rawX, y: rawY });
      setScreenEnd({ x: rawX, y: rawY });
    }
  };

  const handleCanvasMouseMove = (e) => {
    if (isDrawing) {
      const rect = canvasRef.current.getBoundingClientRect();
      const canvas = canvasRef.current;
      
      // Get mouse position relative to the scaled canvas
      const rawX = e.clientX - rect.left;
      const rawY = e.clientY - rect.top;
      
      // Convert from screen coordinates to canvas coordinates
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      
      const x = rawX * scaleX;
      const y = rawY * scaleY;
      
      setSquareEnd({ x, y });
      setScreenEnd({ x: rawX, y: rawY });
    }
  };

  const handleCanvasMouseUp = () => {
    if (isDrawing && squareStart && squareEnd) {
      console.log(`📦 Square drawn from (${squareStart.x}, ${squareStart.y}) to (${squareEnd.x}, ${squareEnd.y})`);
      console.log(`📡 Would send GET request to backend with coordinates: ${JSON.stringify({
        start: squareStart,
        end: squareEnd
      })}`);

      // Trigger analysis on selection using screen coordinates against rendered image
      analyzeSelection();
    }
    setIsDrawing(false);
    setSquareStart(null);
    setSquareEnd(null);
    setScreenStart(null);
    setScreenEnd(null);
  };

  // Chat functionality
  const handleChatSubmit = (e) => {
    e.preventDefault();
    if (chatMessage.trim()) {
      console.log(`💬 Chat message: "${chatMessage}"`);
      console.log(`📡 Would send GET request to backend with query: "${chatMessage}"`);
      setChatMessage('');
    }
  };

  // Draw square on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (squareStart && squareEnd) {
      // Draw directly in canvas coordinates
      // The canvas is already being scaled by CSS, so no need to apply zoom/position here
      const rectX = Math.min(squareStart.x, squareEnd.x);
      const rectY = Math.min(squareStart.y, squareEnd.y);
      const rectWidth = Math.abs(squareEnd.x - squareStart.x);
      const rectHeight = Math.abs(squareEnd.y - squareStart.y);
      
      // Fill with white at 10% opacity
      ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.fillRect(rectX, rectY, rectWidth, rectHeight);
      
      // Red outline
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.strokeRect(rectX, rectY, rectWidth, rectHeight);
    }
  }, [squareStart, squareEnd]);

  // Keep overlay canvas sized to the rendered image size (including zoom scaling at wrapper level)
  useEffect(() => {
    const imgEl = imageRef.current;
    const canvasEl = canvasRef.current;
    if (!imgEl || !canvasEl) return;
    const syncSize = () => {
      const rect = imgEl.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvasEl.style.width = `${rect.width}px`;
      canvasEl.style.height = `${rect.height}px`;
      canvasEl.width = Math.max(1, Math.round(rect.width * dpr));
      canvasEl.height = Math.max(1, Math.round(rect.height * dpr));
    };
    syncSize();
    const ro = new ResizeObserver(syncSize);
    ro.observe(imgEl);
    return () => ro.disconnect();
  }, [currentImage, zoomLevel, lastIntegerZoom, position]);

  // Analyze the selected region by sampling the rendered image
  const analyzeSelection = () => {
    const imgEl = imageRef.current;
    if (!imgEl || !screenStart || !screenEnd) return;

    const imgRect = imgEl.getBoundingClientRect();
    const selX = Math.min(screenStart.x, screenEnd.x);
    const selY = Math.min(screenStart.y, screenEnd.y);
    const selW = Math.abs(screenEnd.x - screenStart.x);
    const selH = Math.abs(screenEnd.y - screenStart.y);
    if (selW < 2 || selH < 2) return;

    // Prepare offscreen canvas matching rendered image size
    let off = offscreenRef.current;
    if (!off) {
      off = document.createElement('canvas');
      offscreenRef.current = off;
    }
    off.width = Math.max(1, Math.round(imgRect.width));
    off.height = Math.max(1, Math.round(imgRect.height));
    const octx = off.getContext('2d');
    octx.clearRect(0, 0, off.width, off.height);
    octx.drawImage(imgEl, 0, 0, off.width, off.height);

    // Sample the selection area
    const sx = Math.max(0, Math.floor(selX));
    const sy = Math.max(0, Math.floor(selY));
    const sw = Math.min(off.width - sx, Math.floor(selW));
    const sh = Math.min(off.height - sy, Math.floor(selH));
    if (sw <= 0 || sh <= 0) return;
    const data = octx.getImageData(sx, sy, sw, sh).data;
    let rSum = 0, gSum = 0, bSum = 0, n = 0;
    for (let i = 0; i < data.length; i += 4) {
      rSum += data[i];
      gSum += data[i + 1];
      bSum += data[i + 2];
      n += 1;
    }
    const avgR = rSum / n;
    const avgG = gSum / n;
    const avgB = bSum / n;
    const scores = computeElementPresence(avgR, avgG, avgB);

    const [rw, gw, bw] = rgbToWavelengths(avgR, avgG, avgB);
    setAnalysisData({
      avgRGB: [avgR, avgG, avgB],
      wavelengths: [rw, gw, bw],
      scores,
    });
    setIsAnalysisOpen(true);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🌌 Intergalactic Zoomer</h1>
        <div className="controls-info">
          <p>Use arrow keys or mouse to move • Mouse wheel to zoom • Ctrl + drag to draw squares</p>
        </div>
      </header>

      <main className="main-content">
        <div className="image-container">
          <div
            className="image-wrapper"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{
              // Scale relative to the last fetched integer zoom (clamped at MAX_INTEGER_ZOOM)
              transform: `translate(${position.x}px, ${position.y}px) scale(${zoomLevel / Math.max(1, Math.min(lastIntegerZoom, MAX_INTEGER_ZOOM))})`,
              cursor: isDragging ? 'grabbing' : 'grab'
            }}
          >
            {currentImage && (
              <img
                ref={imageRef}
                src={currentImage}
                alt="Zoomable image"
                className="main-image"
                draggable={false}
                style={{
                  transformOrigin: 'top left'
                }}
              />
            )}
            <canvas
              ref={canvasRef}
              className="drawing-canvas"
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
            />

            {isAnalysisOpen && analysisData && (
              <div className="analysis-panel">
                <div className="analysis-header">
                  <h4>Element Presence</h4>
                  <button className="analysis-close" onClick={() => setIsAnalysisOpen(false)}>×</button>
                </div>
                <div className="analysis-meta">
                  <span>Avg RGB: {analysisData.avgRGB.map(v => v.toFixed(0)).join(', ')}</span>
                  <span>λ(nm): {analysisData.wavelengths.map(v => v.toFixed(1)).join(', ')}</span>
                </div>
                <svg className="analysis-chart" viewBox="0 0 360 200" preserveAspectRatio="xMidYMid meet">
                  {(() => {
                    const BAR_W = 18;
                    const GAP = 4;
                    const max = Math.max(1, ...analysisData.scores);
                    return analysisData.scores.slice(0, spectralLines.length).map((s, idx) => {
                      const h = (s / max) * 160;
                      const x = 10 + idx * (BAR_W + GAP);
                      const y = 180 - h;
                      return (
                        <g key={idx}>
                          <rect x={x} y={y} width={BAR_W} height={h} fill="#78d3ff" opacity={0.8} />
                          <text x={x + BAR_W / 2} y={190} textAnchor="middle" className="tick">{elementSymbols[idx] || ''}</text>
                        </g>
                      );
                    });
                  })()}
                  <line x1="10" y1="180" x2="350" y2="180" stroke="rgba(255,255,255,0.3)" />
                </svg>
              </div>
            )}
          </div>
        </div>

        <div className="sidebar">
          <div className="zoom-info">
            <h3>Zoom Level</h3>
            <p>{zoomLevel.toFixed(2)}x</p>
            <div className="zoom-controls">
              <button onClick={() => setZoomLevel(prev => Math.max(1, prev - 0.1))}>
                -
              </button>
              <button onClick={() => setZoomLevel(prev => prev + 0.1)}>
                +
              </button>
            </div>
          </div>

          <div className="position-info">
            <h3>Position</h3>
            <p>Screen X: {position.x.toFixed(0)}px</p>
            <p>Screen Y: {position.y.toFixed(0)}px</p>
            {(() => {
              const integerZoom = Math.floor(zoomLevel);
              const clampedZoom = Math.max(1, Math.min(integerZoom, MAX_INTEGER_ZOOM));
              const bx = Math.round((1 - 1/clampedZoom) * 0.5 * IMAGE_WIDTH);
              const by = Math.round((1 - 1/clampedZoom) * 0.5 * IMAGE_HEIGHT);
              return (
                <>
                  <p>Backend X: {bx}</p>
                  <p>Backend Y: {by}</p>
                </>
              );
            })()}
          </div>

          <div className="chat-section">
            <h3>Chat</h3>
            <form onSubmit={handleChatSubmit}>
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Enter your query..."
                className="chat-input"
              />
              <button type="submit" className="chat-submit">
                Send
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
