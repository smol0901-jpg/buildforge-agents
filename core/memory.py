from __future__ import annotations
import json, sqlite3, time, hashlib
from pathlib import Path

def _sig(text: str) -> str:
    norm = " ".join((text or "").lower().split())[:500]
    return hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()[:16]

class Memory:
    def __init__(self, db_path):
        self.path = Path(db_path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row; self._create()
    def _create(self):
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS lessons (
          id INTEGER PRIMARY KEY AUTOINCREMENT, signature TEXT NOT NULL, stack TEXT,
          error_sample TEXT, fix_action TEXT, fix_params TEXT, success INTEGER DEFAULT 0,
          hits INTEGER DEFAULT 1, created_at REAL, updated_at REAL);
        CREATE INDEX IF NOT EXISTS idx_lessons_sig ON lessons(signature);
        CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT, updated_at REAL);
        CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, detail TEXT, ok INTEGER);
        CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, role TEXT, content TEXT);
        """); self._conn.commit()
    def add_action(self, kind, detail, ok=True):
        self._conn.execute("INSERT INTO actions(ts,kind,detail,ok) VALUES (?,?,?,?)", (time.time(), kind, detail[:4000], 1 if ok else 0)); self._conn.commit()
    def record_lesson(self, error_sample, fix_action, fix_params=None, stack="", success=True):
        sig = _sig(error_sample); now = time.time()
        row = self._conn.execute("SELECT id FROM lessons WHERE signature=? AND fix_action=?", (sig, fix_action)).fetchone()
        params = json.dumps(fix_params or {}, ensure_ascii=False)
        if row:
            self._conn.execute("UPDATE lessons SET hits=hits+1, success=?, updated_at=?, error_sample=?, fix_params=?, stack=? WHERE id=?",
                              (1 if success else 0, now, error_sample[:2000], params, stack, row["id"]))
        else:
            self._conn.execute("INSERT INTO lessons(signature,stack,error_sample,fix_action,fix_params,success,hits,created_at,updated_at) VALUES (?,?,?,?,?,?,1,?,?)",
                              (sig, stack, error_sample[:2000], fix_action, params, 1 if success else 0, now, now))
        self._conn.commit()
    def find_lessons(self, error_sample, stack="", limit=5):
        sig = _sig(error_sample)
        rows = self._conn.execute("SELECT * FROM lessons WHERE signature=? OR (stack=? AND success=1) ORDER BY success DESC, hits DESC LIMIT ?", (sig, stack, limit)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try: d["fix_params"] = json.loads(d.get("fix_params") or "{}")
            except Exception: d["fix_params"] = {}
            out.append(d)
        return out
    def set_fact(self, key, value):
        self._conn.execute("INSERT OR REPLACE INTO facts(key,value,updated_at) VALUES (?,?,?)", (key, json.dumps(value, ensure_ascii=False), time.time())); self._conn.commit()
    def get_fact(self, key, default=None):
        row = self._conn.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        if not row: return default
        try: return json.loads(row["value"])
        except Exception: return row["value"]
    def add_message(self, role, content):
        self._conn.execute("INSERT INTO messages(ts,role,content) VALUES (?,?,?)", (time.time(), role, content[:8000])); self._conn.commit()
    def history(self, limit=40):
        rows = self._conn.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return list(reversed([dict(r) for r in rows]))
    def stats(self):
        lessons = self._conn.execute("SELECT COUNT(*) c FROM lessons").fetchone()["c"]
        ok = self._conn.execute("SELECT COUNT(*) c FROM lessons WHERE success=1").fetchone()["c"]
        actions = self._conn.execute("SELECT COUNT(*) c FROM actions").fetchone()["c"]
        return {"lessons": lessons, "successful_lessons": ok, "actions": actions}
