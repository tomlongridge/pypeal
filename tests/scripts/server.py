from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import random


class BellboardMockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/view.php?id='):
            self.respond_with_file(
                os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages', f'{self.path.split("=")[1]}.html')
            )
        elif self.path.startswith('/view.php?random'):
            random_peal_file = random.choice(
                [file for file in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages'))]
            )
            self.send_response(303)
            self.send_header('location', '/view.php?id=' + random_peal_file.split('.')[0])
            self.end_headers()
        elif self.path.startswith('/export.php?'):
            self.respond_with_file(
                os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'searches', '001.xml'),
                'application/xml'
            )
        else:
            self.send_response(404)
            self.end_headers()

    def respond_with_file(self, file: str, content_type: str = 'text/html'):
        with open(file, 'r') as f:
            self.send_response(200)
            self.send_header('Content-type', f'{content_type}; charset=utf-8')
            self.end_headers()
            self.wfile.write(f.read().encode('utf-8'))


server = HTTPServer(('localhost', 8080), BellboardMockServer)
print('Mock server started')
server.serve_forever()
