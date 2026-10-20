from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from controller.mitigation import COOKIE, PRIORITY, install_drop, remove_drop, lab_match

class MitigationTests(unittest.TestCase):
    def setUp(self):
        self.dp = SimpleNamespace(
            ofproto_parser=SimpleNamespace(OFPMatch=lambda **kw: kw, OFPFlowMod=lambda **kw: kw),
            ofproto=SimpleNamespace(OFPFF_SEND_FLOW_REM=1, OFPFC_DELETE_STRICT=4,
                                   OFPP_ANY=0xffffffff, OFPG_ANY=0xffffffff), send_msg=Mock())

    def test_narrow_drop(self):
        rule = install_drop(self.dp, "10.0.0.1", "10.0.0.3", 10)
        self.assertEqual(rule["match"], dict(eth_type=2048, ip_proto=1, ipv4_src="10.0.0.1", ipv4_dst="10.0.0.3"))
        self.assertEqual(rule["instructions"], [])
        self.assertEqual(rule["priority"], PRIORITY)
        self.assertEqual(rule["cookie"], COOKIE)
        self.assertEqual(rule["hard_timeout"], 10)
        self.assertEqual(rule["flags"], 1)
        self.dp.send_msg.assert_called_once_with(rule)

    def test_recovery_delete(self):
        rule = remove_drop(self.dp, "10.0.0.1", "10.0.0.3")
        self.assertEqual(rule["command"], 4)
        self.assertEqual(rule["cookie_mask"], 0xffffffffffffffff)
        self.assertEqual(rule["priority"], PRIORITY)
        self.assertEqual(rule["match"], lab_match("10.0.0.1", "10.0.0.3"))
        self.dp.send_msg.assert_called_once_with(rule)

    def test_invalid_scope(self):
        for source, dest in [("192.0.2.1", "10.0.0.3"), ("10.0.0.1", "192.0.2.1")]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                install_drop(self.dp, source, dest, 10)
        self.dp.send_msg.assert_not_called()

    def test_duration(self):
        for value in [0, 61, True, 1.5]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                install_drop(self.dp, "10.0.0.1", "10.0.0.3", value)

    def test_transport_error(self):
        self.dp.send_msg.side_effect = OSError("disconnected")
        with self.assertRaises(OSError):
            install_drop(self.dp, "10.0.0.1", "10.0.0.3", 10)
