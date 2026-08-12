#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["websockets>=14.0", "zeroconf>=0.80.0", "pywebpush>=2.0.0", "py-vapid>=1.9.0"]
# ///
import importlib
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "relay"))
os.environ.setdefault("HERDR_LOG_DIR", tempfile.mkdtemp(prefix="herdr-relay-test-"))

websockets = types.ModuleType("websockets")
websockets_asyncio = types.ModuleType("websockets.asyncio")
websockets_asyncio_server = types.ModuleType("websockets.asyncio.server")
websockets_server = types.ModuleType("websockets.server")
websockets_exceptions = types.ModuleType("websockets.exceptions")
websockets_asyncio_server.serve = Mock(name="serve")
websockets_server.serve = Mock(name="serve")
websockets_exceptions.ConnectionClosedError = type("ConnectionClosedError", (Exception,), {})
websockets_exceptions.ConnectionClosedOK = type("ConnectionClosedOK", (Exception,), {})
sys.modules.setdefault("websockets", websockets)
sys.modules.setdefault("websockets.asyncio", websockets_asyncio)
sys.modules.setdefault("websockets.asyncio.server", websockets_asyncio_server)
sys.modules.setdefault("websockets.server", websockets_server)
sys.modules.setdefault("websockets.exceptions", websockets_exceptions)

relay = importlib.import_module("herdr_relay")


class RelayWindowsCompatibilityTests(unittest.TestCase):
    def test_windows_log_dir_uses_localappdata(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\styelz\AppData\Local"}, clear=False):
            with patch.object(relay.sys, "platform", "win32"):
                self.assertEqual(
                    relay._get_log_dir(),
                    r"C:\Users\styelz\AppData\Local\herdr-remote\log",
                )

    def test_windows_state_dir_falls_back_when_appdata_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(relay.os.path, "expanduser", return_value=r"C:\Users\styelz"):
                self.assertEqual(
                    relay._windows_state_dir(),
                    r"C:\Users\styelz\AppData\Local\herdr-remote",
                )

    def test_configure_event_loop_policy_switches_windows_to_selector_policy(self):
        selector_policy = object()
        with patch.object(relay.sys, "platform", "win32"):
            with patch.object(relay.asyncio, "WindowsSelectorEventLoopPolicy", return_value=selector_policy, create=True):
                with patch.object(relay.asyncio, "set_event_loop_policy") as set_policy:
                    relay.configure_event_loop_policy()
        set_policy.assert_called_once_with(selector_policy)

    def test_install_signal_handlers_is_disabled_on_windows(self):
        loop = Mock()
        stop = Mock()
        with patch.object(relay.sys, "platform", "win32"):
            self.assertFalse(relay.install_signal_handlers(loop, stop))
        loop.add_signal_handler.assert_not_called()

    def test_install_signal_handlers_registers_sigint_and_sigterm_elsewhere(self):
        loop = Mock()
        stop = Mock()
        with patch.object(relay.sys, "platform", "linux"):
            self.assertTrue(relay.install_signal_handlers(loop, stop))
        self.assertEqual(loop.add_signal_handler.call_count, 2)

    def test_detect_bind_ip_falls_back_to_loopback(self):
        fake_socket = Mock()
        fake_socket.connect.side_effect = OSError("offline")
        with patch.object(relay.socket, "socket", return_value=fake_socket):
            self.assertEqual(relay._detect_bind_ip(), "127.0.0.1")
        fake_socket.close.assert_called_once_with()

    def test_detect_bind_ip_uses_bound_address(self):
        fake_socket = Mock()
        fake_socket.getsockname.return_value = ("192.168.1.25", 50000)
        with patch.object(relay.socket, "socket", return_value=fake_socket):
            self.assertEqual(relay._detect_bind_ip(), "192.168.1.25")
        fake_socket.connect.assert_called_once_with(("8.8.8.8", 80))
        fake_socket.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
