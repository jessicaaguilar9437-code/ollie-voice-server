#!/usr/bin/env python3
import asyncio
import io
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import edge_tts

VOICE = "en-US-AriaNeural"
PORT  = int(os.environ.get("PORT", 5050))


async def _generate(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=VOICE, rate="+15%", pitch="+5%")
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        params = parse_qs(urlparse(self.path).query)
        text = params.get("text", [""])[0].strip()
        if not text:
            self.send_response(400)
            self.end_headers()
            return
        try:
            audio = asyncio.run(_generate(text))
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(audio)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(audio)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"Ollie voice server running on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
