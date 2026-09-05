import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

with get_connection() as conn:
    runs = conn.execute('SELECT run_id, status FROM batch_runs WHERE status = "running"').fetchall()
    for r in runs:
        print('Running:', r['run_id'], '-', r['status'])