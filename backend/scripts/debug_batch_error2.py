import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from scripts.run_batch import BatchRunner
from revflow.db.connection import get_connection

run_id = "RUN-DEBUG-API-001"

async def test():
    # First, manually create the batch_runs record like the API would
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO batch_runs (run_id, started_at, status, event_count, llm_call_count, random_seed, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                "2026-09-04T05:18:00.000000+00:00",
                "running",
                0,
                0,
                42,
                "--no-llm",
            ),
        )
        print("Created batch_runs record")
    
    # Now run the batch runner
    runner = BatchRunner(run_id, use_llm=False, regenerate_dataset=False)
    try:
        result = await runner.run()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())