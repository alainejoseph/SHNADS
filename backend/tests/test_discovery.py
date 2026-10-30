"""Tests for the device discovery endpoints and services."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.services.device_service import DeviceService
from app.services.discovery_service import DiscoveryService
import app.services.discovery_service as discovery_module


@pytest.fixture
def discovery_network(monkeypatch):
    """Keep route tests independent of the machine's real network interfaces."""
    monkeypatch.setattr(
        DiscoveryService,
        "_detect_subnet",
        staticmethod(lambda interface=None: "192.168.1.0/24"),
    )
    monkeypatch.setattr(
        DiscoveryService, "_interface_exists", staticmethod(lambda _interface: True)
    )


@pytest.mark.asyncio
async def test_discovery_routes_registered(client: AsyncClient) -> None:
    """Discovery routes must be registered on the FastAPI application."""
    from app.main import app

    paths = list(app.openapi()["paths"].keys())
    assert "/api/discovery/arp" in paths
    assert "/api/devices/discover" in paths


@pytest.mark.asyncio
async def test_post_arp_discovery_success(client: AsyncClient, test_db, discovery_network) -> None:
    """POST /api/discovery/arp should trigger ARP scan and return discovered devices."""
    mock_scan = [{"ip": "192.168.1.50", "mac": "12:22:33:44:55:66"}]

    with patch.object(DiscoveryService, "_arp_scan", return_value=mock_scan):
        response = await client.post("/api/discovery/arp")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "discovery_complete"
        assert data["devices_found"] == 1
        assert "Discovered 1 device(s)" in data["message"]

    # Verify device persisted into database
    device = await test_db["devices"].find_one({"ip_address": "192.168.1.50"})
    assert device is not None
    assert device["mac_address"] == "12:22:33:44:55:66"
    assert device["source"] == "arp_discovery"


@pytest.mark.asyncio
async def test_post_arp_discovery_with_json_body(client: AsyncClient, test_db, discovery_network) -> None:
    """POST /api/discovery/arp should accept an optional JSON payload with interface."""
    mock_scan = [{"ip": "192.168.1.51", "mac": "12:22:33:44:55:77"}]

    with patch.object(DiscoveryService, "_arp_scan", return_value=mock_scan) as mocked_scan:
        response = await client.post("/api/discovery/arp", json={"interface": "eth0"})
        assert response.status_code == 200
        assert response.json()["devices_found"] == 1

        # Check interface was passed to _arp_scan
        args, _ = mocked_scan.call_args
        assert args[1] == "eth0"


@pytest.mark.asyncio
async def test_post_arp_discovery_with_query_param(client: AsyncClient, test_db, discovery_network) -> None:
    """POST /api/discovery/arp should accept interface as a query parameter."""
    mock_scan = [{"ip": "192.168.1.52", "mac": "12:22:33:44:55:88"}]

    with patch.object(DiscoveryService, "_arp_scan", return_value=mock_scan) as mocked_scan:
        response = await client.post("/api/discovery/arp", params={"interface": "wlan0"})
        assert response.status_code == 200
        assert response.json()["devices_found"] == 1

        args, _ = mocked_scan.call_args
        assert args[1] == "wlan0"


@pytest.mark.asyncio
async def test_post_arp_discovery_error_handling(client: AsyncClient) -> None:
    """POST /api/discovery/arp should return 400 when discovery service reports an error."""
    with patch.object(
        DiscoveryService,
        "discover_devices",
        return_value={"status": "error", "message": "scapy is not installed — ARP discovery unavailable."},
    ):
        response = await client.post("/api/discovery/arp")
        assert response.status_code == 400
        assert "scapy is not installed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_compat_devices_discover_get(client: AsyncClient, test_db, discovery_network) -> None:
    """GET /api/devices/discover must return 200 and delegate to DiscoveryService (fixing 404)."""
    mock_scan = [{"ip": "192.168.1.60", "mac": "aa:bb:cc:dd:ee:ff"}]

    with patch.object(DiscoveryService, "_arp_scan", return_value=mock_scan):
        response = await client.get("/api/devices/discover")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "discovery_complete"
        assert data["devices_found"] == 1


@pytest.mark.asyncio
async def test_compat_devices_discover_post(client: AsyncClient, test_db, discovery_network) -> None:
    """POST /api/devices/discover must return 200 and delegate to DiscoveryService."""
    mock_scan = [{"ip": "192.168.1.61", "mac": "aa:bb:cc:dd:ee:02"}]

    with patch.object(DiscoveryService, "_arp_scan", return_value=mock_scan):
        response = await client.post("/api/devices/discover")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "discovery_complete"
        assert data["devices_found"] == 1


@pytest.mark.asyncio
async def test_get_device_detail_still_works_and_404_on_missing(client: AsyncClient, test_db) -> None:
    """GET /api/devices/{device_key} must continue working and return 404 for unknown devices."""
    service = DeviceService(test_db)
    await service.upsert_device(ip="192.168.1.100", mac="00:11:22:33:44:aa", source="manual")

    # Found
    response = await client.get("/api/devices/192.168.1.100_00:11:22:33:44:aa")
    assert response.status_code == 200
    assert response.json()["ip_address"] == "192.168.1.100"

    # Not found
    response = await client.get("/api/devices/nonexistent_device_key")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


@pytest.mark.asyncio
async def test_remote_website_ips_excluded_from_devices_collection(test_db) -> None:
    """Remote/external website IPs from passive capture must NOT be added to devices collection."""
    service = DeviceService(test_db)

    # 93.184.216.34 is example.com (public IP)
    res = await service.upsert_device(
        ip="93.184.216.34",
        mac="00:11:22:33:44:55",
        source="passive_capture",
    )
    assert res == {}

    # Verify not inserted in DB
    found = await test_db["devices"].find_one({"ip_address": "93.184.216.34"})
    assert found is None


@pytest.mark.asyncio
async def test_user_verified_device_name_preserved(test_db) -> None:
    """User-verified device names must not be overwritten by subsequent discovery or capture."""
    service = DeviceService(test_db)

    # Insert device with user_verified = True and custom name
    dev_key = "192.168.1.75_aa:bb:cc:11:22:33"
    await test_db["devices"].insert_one({
        "device_key": dev_key,
        "ip_address": "192.168.1.75",
        "mac_address": "aa:bb:cc:11:22:33",
        "name": "User Custom Living Room TV",
        "user_verified": True,
        "source": "manual",
    })

    # Upsert from arp_discovery
    await service.upsert_device(
        ip="192.168.1.75",
        mac="aa:bb:cc:11:22:33",
        source="arp_discovery",
        hostname="generic-tv",
        skip_validation=True,
    )

    # Verify name is preserved
    doc = await test_db["devices"].find_one({"device_key": dev_key})
    assert doc is not None
    assert doc["name"] == "User Custom Living Room TV"


def test_detect_subnet_uses_interface_and_monitored_subnet() -> None:
    """DiscoveryService._detect_subnet should prioritize interface and configured subnet."""
    from app.config import Settings

    # Case 1: Configured DISCOVERY_SUBNET
    settings = Settings(DISCOVERY_SUBNET="10.20.30.0/24")
    with patch("app.services.discovery_service.get_settings", return_value=settings):
        subnet = DiscoveryService._detect_subnet(None)
        assert subnet == "10.20.30.0/24"

    # Case 2: Specific interface subnet
    with patch(
        "app.utils.network.get_interface_info",
        return_value={"ip": "172.16.1.10", "netmask": "255.255.255.0", "network": "172.16.1.0/24"},
    ):
        subnet = DiscoveryService._detect_subnet("eth_test")
        assert subnet == "172.16.1.0/24"


def test_arp_scan_retries_only_unanswered_hosts_and_uses_interface(monkeypatch) -> None:
    """Answered hosts are retained and retries target only unanswered hosts."""
    class Packet:
        def __init__(self, payload=None):
            self.payload = payload
        def __truediv__(self, payload):
            return Packet(payload)

    class Layer:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(discovery_module, "Ether", lambda **kw: Packet())
    monkeypatch.setattr(discovery_module, "ARP", lambda **kw: Layer(**kw))
    monkeypatch.setattr(discovery_module, "_SCAPY_AVAILABLE", True)
    monkeypatch.setattr(discovery_module, "get_settings", lambda: type("Cfg", (), {
        "ARP_TIMEOUT": 5, "ARP_RETRIES": 1, "ARP_INTER_RETRY_DELAY": 0,
        "DISCOVERY_MAX_DURATION": 30,
    })())
    monkeypatch.setattr(DiscoveryService, "_interface_exists", lambda iface: iface == "test0")
    calls = []
    def fake_srp(packets, **kwargs):
        calls.append((packets, kwargs))
        if len(calls) == 1:
            first, *rest = packets
            return [(first, Layer(psrc="192.168.2.1", hwsrc="aa:bb:cc:dd:ee:01"))], rest
        return [(packets[0], Layer(psrc="192.168.2.2", hwsrc="aa:bb:cc:dd:ee:02"))], []
    monkeypatch.setattr(discovery_module, "srp", fake_srp)
    monkeypatch.setattr(discovery_module.time, "sleep", lambda _: None)

    result = DiscoveryService._arp_scan("192.168.2.0/30", "test0")

    assert {entry["ip"] for entry in result} == {"192.168.2.1", "192.168.2.2"}
    assert [len(call[0]) for call in calls] == [2, 1]
    assert all(call[1]["iface"] == "test0" and call[1]["timeout"] <= 5 for call in calls)


def test_arp_scan_reports_invalid_interface_and_subnet(monkeypatch) -> None:
    monkeypatch.setattr(discovery_module, "_SCAPY_AVAILABLE", True)
    monkeypatch.setattr(DiscoveryService, "_interface_exists", lambda _: False)
    with pytest.raises(ValueError, match="interface"):
        DiscoveryService._arp_scan("192.168.1.0/24", "missing0")
    with pytest.raises(ValueError, match="subnet"):
        DiscoveryService._arp_scan("0.0.0.0/0")
    with pytest.raises(ValueError, match="subnet"):
        DiscoveryService._arp_scan("10.255.255.254/32")


def test_detect_subnet_rejects_interface_host_route(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.utils.network.get_interface_info",
        lambda _: {"ip": "10.255.255.254", "netmask": "255.255.255.255", "network": "10.255.255.254/32"},
    )
    monkeypatch.setattr(discovery_module, "_NETIFACES_AVAILABLE", False)
    assert DiscoveryService._detect_subnet("vpn0") is None


def test_response_validation_rejects_external_and_malformed_devices() -> None:
    import ipaddress
    network = ipaddress.ip_network("192.168.1.0/24")
    assert DiscoveryService._valid_response("192.168.1.20", "aa:bb:cc:dd:ee:ff", network)
    assert not DiscoveryService._valid_response("8.8.8.8", "aa:bb:cc:dd:ee:ff", network)
    assert not DiscoveryService._valid_response("192.168.1.20", "invalid", network)


def test_arp_scan_reports_scapy_socket_errors(monkeypatch) -> None:
    monkeypatch.setattr(discovery_module, "_SCAPY_AVAILABLE", True)
    monkeypatch.setattr(discovery_module, "get_settings", lambda: type("Cfg", (), {
        "ARP_TIMEOUT": 1, "ARP_RETRIES": 0, "ARP_INTER_RETRY_DELAY": 0,
        "DISCOVERY_MAX_DURATION": 2,
    })())
    monkeypatch.setattr(discovery_module, "Ether", lambda **_: type("Packet", (), {
        "__truediv__": lambda self, payload: type("Packet", (), {"payload": payload})()
    })())
    monkeypatch.setattr(discovery_module, "ARP", lambda **kw: type("ARP", (), kw)())
    monkeypatch.setattr(discovery_module, "srp", lambda *a, **kw: (_ for _ in ()).throw(OSError("permission denied")))
    with pytest.raises(RuntimeError, match="permission denied"):
        DiscoveryService._arp_scan("192.168.1.0/30")


def test_arp_scan_returns_empty_after_configured_retries(monkeypatch) -> None:
    class Packet:
        def __init__(self, payload=None):
            self.payload = payload
        def __truediv__(self, payload):
            return Packet(payload)
    class Layer:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    calls = []
    monkeypatch.setattr(discovery_module, "_SCAPY_AVAILABLE", True)
    monkeypatch.setattr(discovery_module, "Ether", lambda **_: Packet())
    monkeypatch.setattr(discovery_module, "ARP", lambda **kw: Layer(**kw))
    monkeypatch.setattr(discovery_module, "srp", lambda packets, **kwargs: (
        calls.append((packets, kwargs)) or ([], packets)
    ))
    monkeypatch.setattr(discovery_module, "get_settings", lambda: type("Cfg", (), {
        "ARP_TIMEOUT": 5, "ARP_RETRIES": 2, "ARP_INTER_RETRY_DELAY": 0,
        "DISCOVERY_MAX_DURATION": 30,
    })())
    monkeypatch.setattr(discovery_module.time, "sleep", lambda _: None)

    assert DiscoveryService._arp_scan("192.168.2.0/30") == []
    assert len(calls) == 3
    assert [len(call[0]) for call in calls] == [2, 2, 2]


def test_response_processing_deduplicates_and_discards_external_responses() -> None:
    import ipaddress
    network = ipaddress.ip_network("192.168.1.0/24")
    responses = [
        {"ip": "192.168.1.20", "mac": "aa:bb:cc:dd:ee:20"},
        {"ip": "192.168.1.20", "mac": "aa:bb:cc:dd:ee:20"},
        {"ip": "8.8.8.8", "mac": "aa:bb:cc:dd:ee:88"},
    ]
    result = DiscoveryService._unique_valid_responses(responses, network)
    assert list(result) == ["192.168.1.20"]
