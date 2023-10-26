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
            for param in self.path.split('?')[1].split('&'):
                param_name, param_value = param.split('=')
                if param_name == 'ringer':
                    response_file = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'searches', f'{param_value}.xml')
                    if os.path.exists(response_file):
                        self.respond_with_file(response_file, 'application/xml')
                        return
            self.respond_with_content(
                '<performances xmlns="http://bb.ringingworld.co.uk/NS/performances#"></performances>',
                content_type='application/xml')
        else:
            self.send_response(404)
            self.end_headers()

    def respond_with_content(self, content: str, content_type: str = 'text/html'):
        self.send_response(200)
        self.send_header('Content-type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def respond_with_file(self, file: str, content_type: str = 'text/html'):
        if not os.path.exists(file):
            self.send_response(404)
            self.end_headers()
        with open(file, 'r') as f:
            self.respond_with_content(f.read(), content_type=content_type)


server = HTTPServer(('localhost', 8080), BellboardMockServer)
print('Mock server started')
server.serve_forever()
