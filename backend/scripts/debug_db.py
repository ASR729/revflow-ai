import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

with get_connection() as conn:
    # Check batch_runs
    runs = conn.execute('SELECT * FROM batch_runs ORDER BY started_at DESC LIMIT 5').fetchall()
    for r in runs:
        print(f"Run: {dict(r)}")
    
    # Check events
    events = conn.execute('SELECT run_id, COUNT(*) as count FROM events GROUP BY run_id').fetchall()
    for e in events:
        print(f"Events for {e['run_id']}: {e['count']}")