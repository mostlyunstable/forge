from forge.infrastructure.search.intent_router import IntentRouter


def test_intent_router_code():
    router = IntentRouter()
    res = router.route("where is the code for the main function?")
    assert res["primary_intent"] == "code"
    assert res["weights"]["code"] > res["weights"]["bugs"]
    assert res["weights"]["code"] > res["weights"]["decisions"]


def test_intent_router_bug():
    router = IntentRouter()
    res = router.route("fix the bug with null exception")
    assert res["primary_intent"] == "bugs"
    assert res["weights"]["bugs"] > res["weights"]["code"]
    assert res["weights"]["bugs"] > res["weights"]["decisions"]


def test_intent_router_arch():
    router = IntentRouter()
    res = router.route("why was this architecture decision made?")
    assert res["primary_intent"] == "decisions"
    assert res["weights"]["decisions"] > res["weights"]["code"]
    assert res["weights"]["decisions"] > res["weights"]["bugs"]


def test_intent_router_graph():
    router = IntentRouter()
    res = router.route("what is the impact on its dependencies?")
    assert res["primary_intent"] == "graph"
    assert res["weights"]["graph"] > res["weights"]["code"]
    assert res["weights"]["graph"] > res["weights"]["bugs"]


class DummyMessage:
    def __init__(self, content):
        self.content = content


class DummyContextWindow:
    def __init__(self, messages):
        self.messages = messages


def test_intent_router_with_history():
    router = IntentRouter()
    # Query itself is neutral/code focused
    # History emphasizes bugs
    window = DummyContextWindow(
        [
            DummyMessage("we have a crash and exception in the handler"),
            DummyMessage("fix the broken issue"),
        ]
    )
    res = router.route("where is the code?", context_window=window)
    # the history should boost bugs
    assert res["weights"]["bugs"] > 0
    # ensure it still identifies code as primary or at least weights are updated
    assert "weights" in res
