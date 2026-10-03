"""VK-мост без сети: подменяем VK API, ИИ и паузы. Запуск: python tests/test_vk_bridge.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["VK_GROUP_TOKEN"] = "test"
import vk_bridge as V

CALLS = []
V.api = lambda method, **p: CALLS.append((method, p)) or {}
V.time.sleep = lambda s: None
V.AI._call = lambda system, text, max_tokens=0: "" if "спам" in text else ("ответ: " + text[:20])

V.handle({"type": "wall_reply_new", "object": {"from_id": 5, "post_id": 46, "id": 7, "text": "Как красиво"}})
assert CALLS[-1][0] == "wall.createComment" and CALLS[-1][1]["reply_to_comment"] == 7 and CALLS[-1][1]["owner_id"] == -V.GROUP_ID
n = len(CALLS)
V.handle({"type": "wall_reply_new", "object": {"from_id": -V.GROUP_ID, "post_id": 46, "id": 8, "text": "наш ответ"}})
V.handle({"type": "wall_reply_new", "object": {"from_id": 9, "post_id": 46, "id": 9, "text": "купи спам"}})
assert len(CALLS) == n, "ответили себе или на спам"
V.handle({"type": "message_new", "object": {"message": {"from_id": 5, "peer_id": 5, "text": "Хочу письмо маме"}}})
assert CALLS[-1][0] == "messages.send" and CALLS[-1][1]["peer_id"] == 5
print("OK: vk bridge")
