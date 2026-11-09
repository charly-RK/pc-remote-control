from pcremote.application.device_service import DeviceService
from pcremote.application.settings_service import SettingsService
from pcremote.domain.devices import PairedDevice
from pcremote.domain.events import DeviceRevoked

from .fakes import FakeDeviceRepository, FakeSettingsStore, RecordingPublisher


def test_revoke_removes_device_and_publishes():
    repo, bus = FakeDeviceRepository(), RecordingPublisher()
    repo.add(PairedDevice("d1", "Pixel", "h", 1.0, 2.0))
    service = DeviceService(repo, bus)
    assert service.revoke("d1") is True
    assert bus.events == [DeviceRevoked("d1")]
    assert service.revoke("d1") is False and len(bus.events) == 1


def test_list_is_sorted_by_last_seen_desc():
    repo = FakeDeviceRepository()
    repo.add(PairedDevice("a", "A", "h1", 1.0, 5.0))
    repo.add(PairedDevice("b", "B", "h2", 1.0, 9.0))
    assert [d.device_id for d in DeviceService(repo, RecordingPublisher()).list_devices()] == ["b", "a"]


def test_settings_generate_server_id_once_and_persist_updates():
    store = FakeSettingsStore()
    service = SettingsService(store)
    server_id = service.settings.server_id
    assert server_id and store.settings.server_id == server_id
    service.update(minimize_to_tray=False)
    assert store.settings.minimize_to_tray is False
    assert SettingsService(store).settings.server_id == server_id
