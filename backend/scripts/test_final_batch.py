import asyncio
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_batch import BatchRunner

run_id = "RUN-DEBUG-PHASE6-10"
print(f"Running batch with run_id: {run_id} (offline mode)")

async def test():
    runner = BatchRunner(run_id, use_llm=False, regenerate_dataset=False)
    result = await runner.run()
    print(result)
    
    from revflow.metrics.summary import compute_summary_metrics
    import json
    m = compute_summary_metrics(run_id)
    print(json.dumps(m, indent=2))

asyncio.run(test())