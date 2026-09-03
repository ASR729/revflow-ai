import os
import signal
import subprocess

# Kill any uvicorn processes
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

# Also kill python processes that might be holding the db
for proc in os.popen('tasklist /FI "IMAGENAME eq python.exe"').read().splitlines():
    if 'python.exe' in proc:
        parts = proc.split()
        if len(parts) > 1:
            pid = int(parts[1])
            if pid != os.getpid():
                print('Killing PID', pid)
                try:
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass

print('Killed uvicorn/python processes')