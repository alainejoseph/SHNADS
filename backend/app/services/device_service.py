"""Device service — business logic for device management."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class DeviceService:
    """Manages device CRUD operations against MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._collection = db["devices"]

    async def upsert_device(
        self,
        ip: str,
        mac: Optional[str],
        source: str,
        hostname: Optional[str] = None,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """Insert a new device or update an existing one.

        The ``device_key`` is computed as ``"{ip}_{mac}"`` when a MAC address
        is available, or simply ``"{ip}"`` otherwise.  If the device already
        exists the ``last_seen`` timestamp is refreshed and new fields are
        merged; otherwise a fresh document is created.

        Args:
            ip: IP address of the device.
            mac: MAC address (may be ``None``).
            source: Discovery source identifier.
            hostname: Optional resolved hostname.

        Returns:
            The upserted device document as a dict.
        """
        from app.utils.network import get_local_networks, is_ip_in_monitored_network, is_likely_external
        import ipaddress

        # Validate IP is in monitored network unless explicitly skipped (e.g., for manual entries)
        if not skip_validation:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_loopback or ip_obj.is_unspecified or ip_obj.is_multicast:
                    logger.warning("Skipping device creation for invalid/special IP: %s", ip)
                    return {}
                # For non-discovery sources, be stricter - only allow if in monitored network
                if source in ("passive_capture",):
                    networks = get_local_networks()
                    if networks and not is_ip_in_monitored_network(ip, networks):
                        logger.debug("Skipping device creation for external IP %s from %s", ip, source)
                        return {}
            except Exception:
                pass

        device_key = f"{ip}_{mac}" if mac else ip
        now = datetime.utcnow()

        # Try to preserve user-verified names by looking up existing doc
        existing = await self._collection.find_one({"device_key": device_key})
        user_verified_name = None
        if existing and existing.get("user_verified"):
            user_verified_name = existing.get("name")

        update: Dict[str, Any] = {
            "$set": {
                "ip_address": ip,
                "last_seen": now,
            },
            "$setOnInsert": {
                "device_key": device_key,
                "first_seen": now,
                "metadata": {},
                "source": source,
            },
        }

        if mac is not None:
            update["$set"]["mac_address"] = mac
        if hostname is not None and not (existing and existing.get("hostname")):
            update["$set"]["hostname"] = hostname
        if user_verified_name:
            update["$set"]["name"] = user_verified_name

        try:
            result = await self._collection.update_one(
                {"device_key": device_key},
                update,
                upsert=True,
            )
        except Exception as exc:
            logger.error("Error upserting device %s: %s", device_key, exc)
            raise

        doc = await self._collection.find_one({"device_key": device_key})
        if doc:
            doc.pop("_id", None)

        logger.debug(
            "Upserted device %s (matched=%s, modified=%s, upserted=%s)",
            device_key,
            result.matched_count,
            result.modified_count,
            result.upserted_id is not None,
        )
        return doc or {}

    async def list_devices(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Return a paginated list of devices, optionally filtered by search.

        The ``search`` parameter matches against ``ip_address``,
        ``mac_address``, and ``hostname`` using a case-insensitive regex.

        Args:
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            search: Optional search string.

        Returns:
            A tuple of (list of device dicts, total matching count).
        """
        query: Dict[str, Any] = {}
        if search:
            regex = {"$regex": search, "$options": "i"}
            query["$or"] = [
                {"ip_address": regex},
                {"mac_address": regex},
                {"hostname": regex},
            ]

        total = await self._collection.count_documents(query)
        cursor = (
            self._collection.find(query, {"_id": 0})
            .sort("last_seen", -1)
            .skip(skip)
            .limit(limit)
        )
        devices = await cursor.to_list(length=limit)
        return devices, total

    async def get_device(self, device_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single device by its key.

        Args:
            device_key: The unique device key.

        Returns:
            The device document or ``None`` if not found.
        """
        doc = await self._collection.find_one(
            {"device_key": device_key}, {"_id": 0}
        )
        return doc

