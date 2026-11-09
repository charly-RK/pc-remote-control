import pytest

from pcremote.application.auth_service import AuthService, hash_token
from pcremote.domain.errors import InvalidPinError, InvalidTokenError, RateLimitedError
from pcremote.domain.events import ClientAuthenticated, DevicePaired
from pcremote.domain.session import ClientSession

from .fakes import FakeClock, FakeDeviceRepository, FakePinStore, RecordingPublisher


def make(pin="123456"):
    store, bus, clock = FakePinStore(pin), RecordingPublisher(), FakeClock()
    auth = AuthService(store, FakeDeviceRepository(), bus, clock=clock)
    return auth, store, bus, clock


def session(ip="10.0.0.2"):
    return ClientSession("sid-1", ip)


def test_generates_six_digit_pin_and_persists_it():
    auth, store, _, _ = make(pin=None)
    pin = auth.ensure_pin()
    assert len(pin) == 6 and pin.isdigit()
    assert store.pin == pin


def test_loads_stored_pin():
    auth, _, _, _ = make("654321")
    assert auth.ensure_pin() == "654321"


def test_success_marks_session_and_publishes_event():
    auth, _, bus, _ = make()
    s = session()
    auth.authenticate(s, "123456", "Pixel")
    assert s.authenticated and s.device_name == "Pixel"
    assert ClientAuthenticated("sid-1", "Pixel") in bus.events
    assert any(isinstance(e, DevicePaired) for e in bus.events)


def test_wrong_pin_is_rejected():
    auth, _, bus, _ = make()
    s = session()
    with pytest.raises(InvalidPinError):
        auth.authenticate(s, "000000", "x")
    assert not s.authenticated and bus.events == []


def test_lock_after_max_attempts_then_unlocks():
    auth, _, _, clock = make()
    s = session()
    for _ in range(4):
        with pytest.raises(InvalidPinError):
            auth.authenticate(s, "000000", None)
    with pytest.raises(RateLimitedError):
        auth.authenticate(s, "000000", None)
    assert auth.is_locked(s.ip)
    with pytest.raises(RateLimitedError):
        auth.authenticate(s, "123456", None)  # correct PIN still refused while locked
    clock.now += 61
    assert not auth.is_locked(s.ip)
    auth.authenticate(s, "123456", None)
    assert s.authenticated


def test_release_pin_clears_store():
    auth, store, _, _ = make()
    auth.ensure_pin()
    auth.release_pin()
    assert auth.pin is None and store.cleared


def test_pairing_returns_token_and_stores_only_its_hash():
    auth, _, _, _ = make()
    s = session()
    result = auth.authenticate(s, "123456", "Pixel")
    assert s.device_id == result.device_id
    stored = auth._devices.list()[0]
    assert stored.token_hash == hash_token(result.token) and result.token not in stored.token_hash


def test_token_reconnect_without_pin():
    auth, _, _, _ = make()
    result = auth.authenticate(session(), "123456", "Pixel")
    other = ClientSession("sid-2", "10.0.0.2")
    device = auth.authenticate_token(other, result.token)
    assert other.authenticated and other.device_id == device.device_id == result.device_id


def test_invalid_token_and_lockout_counts_token_failures():
    auth, _, _, _ = make()
    s = session()
    for _ in range(4):
        with pytest.raises(InvalidTokenError):
            auth.authenticate_token(s, "nope")
    with pytest.raises(RateLimitedError):
        auth.authenticate_token(s, "nope")


def test_revoked_device_token_stops_working():
    auth, _, _, _ = make()
    result = auth.authenticate(session(), "123456", "Pixel")
    auth._devices.remove(result.device_id)
    with pytest.raises(InvalidTokenError):
        auth.authenticate_token(ClientSession("sid-3", "10.0.0.9"), result.token)
