import unittest

from src import gmail_ops


class FakeRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeMessages:
    def __init__(self, pages, snippets=None, batch_calls=None):
        self.pages = pages
        self.snippets = snippets or {}
        self.batch_calls = batch_calls if batch_calls is not None else []

    def list(self, userId=None, q=None, pageToken=None, maxResults=None):  # noqa: N802
        # Return page by token
        page = self.pages.get(pageToken or "page1")
        return FakeRequest(page)

    def get(self, userId=None, id=None, format=None):  # noqa: N802, A002
        res = {"id": id, "snippet": self.snippets.get(id, "")}
        return FakeRequest(res)

    def batchModify(self, userId=None, body=None):  # noqa: N802
        self.batch_calls.append({"userId": userId, "body": body})
        return FakeRequest({})


class FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):  # noqa: D401
        return self._messages


class FakeService:
    def __init__(self, messages):
        self._users = FakeUsers(messages)

    def users(self):
        return self._users


class GmailOpsTest(unittest.TestCase):
    def test_search_message_ids_pagination_and_limit(self):
        pages = {
            "page1": {
                "messages": [{"id": "m1"}, {"id": "m2"}],
                "nextPageToken": "page2",
            },
            "page2": {
                "messages": [{"id": "m3"}, {"id": "m4"}],
            },
        }
        svc = FakeService(FakeMessages(pages))
        ids = gmail_ops.search_message_ids(svc, "me", "q")
        self.assertEqual(ids, ["m1", "m2", "m3", "m4"])

        ids2 = gmail_ops.search_message_ids(svc, "me", "q", limit=3)
        self.assertEqual(ids2, ["m1", "m2", "m3"])

    def test_move_to_trash_batching(self):
        # 2500 messages should trigger 3 batch calls with BATCH_SIZE=1000
        ids = [f"m{i}" for i in range(2500)]
        fm = FakeMessages(pages={})
        svc = FakeService(fm)
        moved = gmail_ops.move_to_trash_batch(svc, "me", ids)
        self.assertEqual(moved, 2500)
        self.assertEqual(len(fm.batch_calls), 3)
        # validate first/last batch sizes
        self.assertEqual(len(fm.batch_calls[0]["body"]["ids"]), 1000)
        self.assertEqual(len(fm.batch_calls[2]["body"]["ids"]), 500)

    def test_get_snippets_samples(self):
        snippets = {"m1": "hello", "m2": "world", "m3": "!", "m4": "extra"}
        fm = FakeMessages(pages={}, snippets=snippets)
        svc = FakeService(fm)
        res = gmail_ops.get_snippets(svc, "me", ["m1", "m2", "m3", "m4"], sample=3)
        self.assertEqual(len(res), 3)
        self.assertTrue(res[0].startswith("[m1] "))


if __name__ == "__main__":
    unittest.main()
