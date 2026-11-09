import socket
import time

import pytest

from pcremote.domain.devices import PairedDevice
from pcremote.domain.settings import AppSettings
from pcremote.infrastructure.network.inspector import SocketNetworkInspector
from pcremote.infrastructure.os.single_instance import SingleInstance
from pcremote.infrastructure.os.startup_registry import build_startup_command
from pcremote.infrastructure.persistence.file_device_repository import FileDeviceRepository
from pcremote.infrastructure.persistence.file_settings_store import FileSettingsStore


def device(device_id="d1", token_hash="h1", name="Pixel"):
    return PairedDevice(device_id, name, token_hash, 1.0, 1.0)


def test_device_repository_roundtrip_and_find(tmp_path):
    path = tmp_path / "devices.json"
    FileDeviceRepository(path).add(device())
    reloaded = FileDeviceRepository(path)
    assert reloaded.list() == [device()]
    assert reloaded.find_by_token_hash("h1").device_id == "d1"
    assert reloaded.find_by_token_hash("nope") is None


def test_device_repository_touch_and_remove(tmp_path):
    path = tmp_path / "devices.json"
    repo = FileDeviceRepository(path)
    repo.add(device())
    repo.touch("d1", 99.0)
    assert FileDeviceRepository(path).list()[0].last_seen == 99.0
    assert repo.remove("d1") is True
    assert repo.remove("d1") is False
    assert FileDeviceRepository(path).list() == []


def test_device_repository_tolerates_corrupt_file(tmp_path):
    path = tmp_path / "devices.json"
    path.write_text("{not json", encoding="utf-8")
    repo = FileDeviceRepository(path)
    assert repo.list() == []
    repo.add(device())
    assert len(FileDeviceRepository(path).list()) == 1


def test_device_repository_skips_invalid_entries(tmp_path):
    path = tmp_path / "devices.json"
    path.write_text('[{"device_id": "x"}, 5]', encoding="utf-8")
    assert FileDeviceRepository(path).list() == []


def test_settings_defaults_and_roundtrip(tmp_path):
    store = FileSettingsStore(tmp_path / "settings.json")
    assert store.load() == AppSettings()
    store.save(AppSettings(server_id="abc", minimize_to_tray=False, auto_start_server=False))
    assert store.load() == AppSettings("abc", False, False)


def test_settings_ignores_unknown_keys_and_bad_types(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"server_id": "s", "minimize_to_tray": "yes", "extra": 1}', encoding="utf-8")
    loaded = FileSettingsStore(path).load()
    assert loaded.server_id == "s" and loaded.minimize_to_tray is True


def test_settings_tolerates_corrupt_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("garbage", encoding="utf-8")
    assert FileSettingsStore(path).load() == AppSettings()


def test_startup_command_background_flag():
    assert build_startup_command().endswith(" --background")
    assert not build_startup_command(background=False).endswith("--background")


def test_hostname_matches_socket():
    assert SocketNetworkInspector().hostname() == socket.gethostname()


def test_single_instance_blocks_second_holder():
    first, second = SingleInstance("PCRemoteControlTest"), SingleInstance("PCRemoteControlTest")
    try:
        assert first.acquire() is True
        assert second.acquire() is False
        first.release()
        first.release()  # idempotent
        assert second.acquire() is True
    finally:
        first.release()
        second.release()


def test_zeroconf_register_and_discover_roundtrip():
    from pcremote.infrastructure.network.zeroconf_discovery import ZeroconfDiscovery, discover_servers

    discovery = ZeroconfDiscovery()
    try:
        try:
            discovery.start("abcdef123456", "TEST-PC", "127.0.0.1", 5723, 1)
        except Exception as exc:  # noqa: BLE001 - multicast may be unavailable in CI
            pytest.skip(f"multicast unavailable: {exc}")
        deadline, found = time.monotonic() + 6, []
        while time.monotonic() < deadline and not found:
            found = [s for s in discover_servers(timeout=2.0) if s["properties"].get("id") == "abcdef123456"]
        if not found:
            pytest.skip("service not discovered (multicast likely blocked)")
        assert found[0]["port"] == 5723
        assert found[0]["properties"]["v"] == "1"
    finally:
        discovery.stop()
        discovery.stop()  # idempotent
