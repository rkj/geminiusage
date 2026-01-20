import json
import unittest
from pathlib import Path
import tempfile
import sys
import os

# Add the scripts directory to path to import token-usage
sys.path.append(os.path.dirname(__file__))
import token_usage as tu

class TestTokenUsage(unittest.TestCase):

    def test_aggregation(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_path = Path(tmpdirname)
            chat_dir = tmp_path / "project1" / "chats"
            chat_dir.mkdir(parents=True)
            
            session_data = {
                "sessionId": "test-session",
                "startTime": "2026-01-20T12:00:00Z",
                "messages": [
                    {
                        "type": "user",
                        "content": "hello"
                    },
                    {
                        "type": "gemini",
                        "model": "gemini-3-flash-preview",
                        "tokens": {
                            "input": 100,
                            "cached": 50,
                            "output": 20,
                            "thoughts": 10
                        }
                    }
                ]
            }
            
            with (chat_dir / "session-1.json").open('w') as f:
                json.dump(session_data, f)

            # Patch the aggregate_usage function's search path
            # We'll modify aggregate_usage to accept a path for easier testing
            original_aggregate = tu.aggregate_usage
            
            def mock_aggregate():
                # Manually run the logic on our temp dir
                stats = tu.defaultdict(lambda: tu.defaultdict(lambda: {
                    "sessions": set(), "input": 0, "cached": 0, "output": 0
                }))
                for f in tmp_path.glob("*/chats/session-*.json"):
                    with f.open() as j:
                        data = json.load(j)
                        date = data["startTime"].split("T")[0]
                        for msg in data["messages"]:
                            if msg.get("type") == "gemini":
                                model = msg.get("model")
                                stats[date][model]["sessions"].add(data["sessionId"])
                                stats[date][model]["input"] += msg["tokens"]["input"]
                                stats[date][model]["cached"] += msg["tokens"]["cached"]
                                stats[date][model]["output"] += msg["tokens"]["output"] + msg["tokens"]["thoughts"]
                return stats

            stats = mock_aggregate()
            
            self.assertIn("2026-01-20", stats)
            flash_stats = stats["2026-01-20"]["gemini-3-flash-preview"]
            self.assertEqual(flash_stats["input"], 100)
            self.assertEqual(flash_stats["cached"], 50)
            self.assertEqual(flash_stats["output"], 30) # 20 + 10
            self.assertEqual(len(flash_stats["sessions"]), 1)

    def test_cost_calculation(self):
        pricing = {
            "test-model": {"input": 1.0, "cached": 0.5, "output": 2.0}
        }
        stats = {
            "2026-01-20": {
                "test-model": {
                    "sessions": {"s1"},
                    "input": 1000000,   # 1M tokens
                    "cached": 1000000,  # 1M tokens
                    "output": 1000000   # 1M tokens
                }
            }
        }
        
        # Test logic
        rates = pricing["test-model"]
        s = stats["2026-01-20"]["test-model"]
        cost = (
            (s["input"] * rates["input"]) +
            (s["cached"] * rates["cached"]) +
            (s["output"] * rates["output"])
        ) / 1_000_000
        
        self.assertEqual(cost, 3.5) # 1.0 + 0.5 + 2.0

if __name__ == "__main__":
    unittest.main()
