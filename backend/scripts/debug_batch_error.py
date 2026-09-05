import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from scripts.run_batch import BatchRunner

run_id = "RUN-DEBUG-20260904T051800"

async def test():
    runner = BatchRunner(run_id, use_llm=False, regenerate_dataset=False)
    try:
        result = await runner.run()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())