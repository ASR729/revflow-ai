@echo off
cd /d C:\Users\asifr\revflow\backend
python -c "import uvicorn; from revflow.main import app; uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')"