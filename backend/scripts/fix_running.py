import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

with get_connection() as conn:
    conn.execute("UPDATE batch_runs SET status = 'failed' WHERE status = 'running'")
    print('Fixed running batch runs')