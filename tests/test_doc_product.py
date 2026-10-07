"""PDF «Разговор с папой»: заказ -> выдача файла после оплаты (без сети). Запуск: python tests/test_doc_product.py"""
import os
import sys
import tempfile
import types as pytypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("TG_BOT_TOKEN", "123:TEST")
os.environ["ADMIN_ID"] = "1"
os.environ["YOOKASSA_PROVIDER_TOKEN"] = "tok"
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = ""

import bot_best as B  # noqa: E402

SENT = []


def rec(name):
    def f(*a, **k):
        SENT.append((name, a, k))
        return pytypes.SimpleNamespace(message_id=len(SENT), chat=pytypes.SimpleNamespace(id=500))
    return f


for m in ["send_message", "send_photo", "send_invoice", "send_document", "answer_callback_query"]:
    setattr(B.bot, m, rec(m))

user = pytypes.SimpleNamespace(id=500, first_name="Аня", username="anya", last_name=None, language_code="ru")
B.occ_doc_order(500, user)
orders = [o for o in B.all_orders() if o.get("product") == B.OCC.DOC["key"]]
assert len(orders) == 1 and orders[0]["price_rub"] == 149, orders
assert any(n == "send_invoice" for n, *_ in SENT), "нет окна оплаты"
assert os.path.exists(os.path.join(os.path.dirname(B.FREE_PDF_PATH), B.OCC.DOC["file"])), "нет файла"
SENT.clear()
B.fulfill_order(500, orders[0]["order_id"], "ch-1", None)
docs = [s for s in SENT if s[0] == "send_document"]
assert len(docs) == 1, SENT
assert B.get_order(orders[0]["order_id"])["status"] == "done"
print("OK: doc product")
