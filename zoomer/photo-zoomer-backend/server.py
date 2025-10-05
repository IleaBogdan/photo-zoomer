#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import json
from io import BytesIO
from interface import get_stitched_image

# Image dimensions from FITS file
IMAGE_WIDTH = 12200
IMAGE_HEIGHT = 8600
W_RESOLUTION = 1920
H_RESOLUTION = 1080

class ImageServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Enable CORS for frontend
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        if parsed_path.path == '/image':
            # Parse query parameters
            query_params = parse_qs(parsed_path.query)
            
            try:
                zoom = int(query_params.get('zoom', [1])[0])
                x = int(query_params.get('x', [0])[0])
                y = int(query_params.get('y', [0])[0])
                
                if zoom == 1:
                    # For 1x zoom, serve the pre-generated static file directly
                    filename = f'assets/test_compression_level_1_x_0_y_0.jpg'
                    if os.path.exists(filename):
                        with open(filename, 'rb') as f:
                            img_bytes = f.read()
                        
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(img_bytes)))
                        self.end_headers()
                        self.wfile.write(img_bytes)
                    else:
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        response = {'error': f'1x image not found: {filename}'}
                        self.wfile.write(json.dumps(response).encode())
                else:
                    # For zoom > 1x, use get_stitched_image to dynamically stitch tiles
                    # This allows for arbitrary x,y positions based on panning
                    img = get_stitched_image(
                        x=x,
                        y=y,
                        zoom_level=zoom,
                        w_resolution=W_RESOLUTION,
                        h_resolution=H_RESOLUTION,
                        w_img=IMAGE_WIDTH,
                        h_img=IMAGE_HEIGHT
                    )
                    
                    # Convert PIL Image to JPEG bytes
                    buf = BytesIO()
                    img.save(buf, format='JPEG', quality=95)
                    img_bytes = buf.getvalue()
                    
                    # Serve the image
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(img_bytes)))
                    self.end_headers()
                    self.wfile.write(img_bytes)
                
            except Exception as e:
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/image-info':
            # Return information about available zoom levels and image dimensions
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Get list of available images in assets directory
            assets_dir = 'assets'
            available_files = [f for f in os.listdir(assets_dir) if f.startswith('test_compression_level_')]
            
            # Extract unique zoom levels and coordinates
            zoom_levels = set()
            coordinates = {}
            
            for filename in available_files:
                parts = filename.replace('.jpg', '').split('_')
                try:
                    zoom_idx = parts.index('level') + 1
                    x_idx = parts.index('x') + 1
                    y_idx = parts.index('y') + 1
                    
                    zoom = int(parts[zoom_idx])
                    x = int(parts[x_idx])
                    y = int(parts[y_idx])
                    
                    zoom_levels.add(zoom)
                    
                    if zoom not in coordinates:
                        coordinates[zoom] = []
                    coordinates[zoom].append({'x': x, 'y': y})
                except (ValueError, IndexError):
                    continue
            
            response = {
                'zoom_levels': sorted(list(zoom_levels)),
                'coordinates': coordinates
            }
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'NASA Image Zoomer API\n\nEndpoints:\n  /image?zoom=X&x=Y&y=Z\n  /image-info')
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom log format
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ImageServer)
    print(f'🚀 NASA Image Server running on http://localhost:{port}')
    print(f'📡 Endpoints:')
    print(f'   - http://localhost:{port}/image?zoom=1&x=0&y=0')
    print(f'   - http://localhost:{port}/image-info')
    httpd.serve_forever()

if __name__ == '__main__':
    # Change to the script's directory so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_server()
