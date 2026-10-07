from http.server import ThreadingHTTPServer
import os
from input_gateway import Handler
host='0.0.0.0'; port=int(os.environ.get('PORT','10000'))
print(f'CURRENT_COMPOSER_START host={host} port={port}',flush=True)
ThreadingHTTPServer((host,port),Handler).serve_forever()
