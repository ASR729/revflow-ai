import sys
sys.path.insert(0, '.')
import subprocess
import os
import signal
import time

# Kill existing uvicorn processes
for proc in os.popen('tasklist /FI "IMAGENAME eq uvicorn.exe"').read().splitlines():
    if 'uvicorn.exe' in proc:
        parts = proc.split()
        if len(parts) > 1:
            pid = int(parts[1])
            print('Killing PID', pid)
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass

print('Starting fresh server...')
proc = subprocess.Popen(['.\\venv\\Scripts\\uvicorn.exe', 'revflow.main:app', '--host', '127.0.0.1', '--port', '8001'], cwd='C:\\Users\\asifr\\revflow\\backend')
time.sleep(3)
print('Server started')

import httpx
r = httpx.get('http://127.0.0.1:8001/health')
print('/health:', r.status_code, r.json())