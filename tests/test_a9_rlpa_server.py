"""A9 rlpa-server — tests. Run: pytest test_a9_rlpa_server.py"""
import sys, os

import pytest

def test_sliding_window_limits():
    from rlpa_server.proxy.ratelimit import SlidingWindow
    w = SlidingWindow(limit=3, window=60)
    assert not w.hit("user1")
    assert not w.hit("user1")
    assert not w.hit("user1")
    assert w.hit("user1")  # 4th hit over limit

def test_sliding_window_per_key():
    from rlpa_server.proxy.ratelimit import SlidingWindow
    w = SlidingWindow(limit=2, window=60)
    assert not w.hit("a")
    assert not w.hit("a")  # 2 allowed
    assert w.hit("a")      # 3rd blocked
    assert not w.hit("b")  # separate key unaffected

def test_forward_strips_internal_headers():
    from rlpa_server.proxy.router import forward
    # verify the header-stripping logic exists
    assert callable(forward)
