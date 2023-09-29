from http.server import BaseHTTPRequestHandler, HTTPServer
import os


class BellboardMockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/view.php?id='):
            peal_file = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages', f'{self.path.split("=")[1]}.html')
            with open(peal_file, 'r') as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(f.read().encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(('localhost', 8080), BellboardMockServer)
print('Mock server started')
server.serve_forever()
