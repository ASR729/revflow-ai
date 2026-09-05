import uvicorn
import asyncio
import requests
import time
from revflow.main import app

async def test_api():
    # Start server in background
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="debug")
    server = uvicorn.Server(config)
    
    # Start server in background
    server_task = asyncio.create_task(server.serve())
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    try:
        # Test the API
        print("Testing POST /run-batch...")
        resp = requests.post("http://127.0.0.1:8000/run-batch", 
                           json={"use_llm": False, "regenerate_dataset": False}, 
                           timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 202:
            data = resp.json()
            run_id = data.get('run_id')
            print(f"Run ID: {run_id}")
            
            # Wait for batch to process
            time.sleep(5)
            
            # Check runs
            resp2 = requests.get("http://127.0.0.1:8000/runs", timeout=10)
            if resp2.status_code == 200:
                for r in resp2.json().get('runs', []):
                    if r['run_id'] == data.get('run_id'):
                        print(f"Run status: {r['status']}")
                        break
        
        if resp.status_code != 202:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Shutdown server
        server.should_exit = True
        await server_task

if __name__ == "__main__":
    import requests
    import time
    asyncio.run(test_api())