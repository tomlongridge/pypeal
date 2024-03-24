from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import random
import urllib.parse


class BellboardMockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/view.php?id='):
            peal_file_name = self.path.split("=")[1]
            peal_file_name = peal_file_name.zfill(7) + '.html'
            self.respond_with_file(
                os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages', peal_file_name)
            )
        elif self.path.startswith('/view.php?random'):
            random_peal_file = random.choice(
                [file for file in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages'))]
            )
            self.send_response(303)
            self.send_header('location', '/view.php?id=' + random_peal_file.split('.')[0])
            self.end_headers()
        elif self.path.startswith('/search.php?'):
            params = urllib.parse.parse_qs(self.path.split('?')[1])
            if 'page' in params:
                page = int(params['page'][0])
            else:
                page = 1
            response_file = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'searches', f'{page}.xml')
            if os.path.exists(response_file):
                self.respond_with_file(response_file, 'application/xml')
                return
            self.respond_with_content(
                '<performances xmlns="http://bb.ringingworld.co.uk/NS/performances#"></performances>',
                content_type='application/xml')
        elif self.path.startswith('/uploads'):
            with open(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals') + self.path, 'rb') as f:
                self.respond_with_content(f.read(), content_type='image/jpeg', encoding=None)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/submit.php'):
            with open(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'submitted', '001.txt'), 'r') as f:
                expected_content = f.read()
                actual_content = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
                if expected_content == actual_content:
                    self.respond_with_file(
                        os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'submitted', 'response.html')
                    )
                    self.send_response(200)
                else:
                    self.respond_with_content('Unexpected peal submit content:' +
                                              f'\n\nActual:\n\n{actual_content}\n\n' +
                                              f'Expected:\n\n{expected_content}',
                                              content_type='text/plain',
                                              status_code=400)
            self.end_headers()
        elif self.path.startswith('/login.php'):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Login successful')
        else:
            self.send_response(404)
            self.end_headers()

    def respond_with_content(self, content: str, status_code: int = 200, content_type: str = 'text/html', encoding: str = 'utf-8'):
        self.send_response(status_code)
        self.send_header('Content-type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode(encoding) if encoding is not None else content)

    def respond_with_file(self, file: str, content_type: str = 'text/html'):
        if not os.path.exists(file):
            self.send_response(404)
            self.end_headers()
        with open(file, 'r') as f:
            self.respond_with_content(f.read(), content_type=content_type)


server = HTTPServer(('localhost', 8080), BellboardMockServer)
print('Mock server started')
server.serve_forever()
