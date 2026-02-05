import os
import sys


# Provide safe defaults for config-driven imports during tests.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("GEMINI_MODEL", "test-model")
os.environ.setdefault("SERPAPI_API_KEY", "test-key")
os.environ.setdefault("OPIK_TRACK_DISABLE", "true")

# Ensure backend/ is on sys.path so tests can import agents.* modules.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# The tests/agents package name shadows backend/agents. Force "agents" to
# resolve to backend/agents for imports like agents.challenge_agent.
BACKEND_AGENTS_DIR = os.path.join(BACKEND_DIR, "agents")
if os.path.isdir(BACKEND_AGENTS_DIR):
    agents_module = type(sys)("agents")
    agents_module.__path__ = [BACKEND_AGENTS_DIR]
    sys.modules["agents"] = agents_module
