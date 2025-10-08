#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend files
Run this script to serve the frontend on localhost:8080
"""

import http.server
import socketserver
import os
import sys

import os

PORT = int(os.getenv("PORT", 8080))  # Cloud Run compatibility

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # If requesting root, serve login.html
        if self.path == '/':
            self.path = '/login.html'
        return super().do_GET()

if __name__ == "__main__":
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}")
        print("Default page: login.html")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
