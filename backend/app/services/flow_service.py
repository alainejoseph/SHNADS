"""Flow service — business logic for network flow management."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.flow import FlowFilters

logger = logging.getLogger(__name__)


class FlowService:
    """Manages flow CRUD operations and aggregation pipelines."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._collection = db["flows"]

    async def store_flows(self, flows: List[Dict[str, Any]]) -> int:
        """Bulk-insert flow documents into MongoDB.

        Args:
            flows: A list of flow dicts ready for insertion.

        Returns:
            The number of documents inserted.
        """
        if not flows:
            return 0

        from datetime import datetime

        cleaned = []
        for f in flows:
            doc = dict(f)
            if "timestamp" not in doc or doc["timestamp"] is None:
                if doc.get("end_time"):
                    ts = doc["end_time"]
                elif doc.get("start_time"):
                    ts = doc["start_time"]
                else:
                    ts = datetime.utcnow().timestamp()
                if isinstance(ts, (int, float)):
                    try:
                        doc["timestamp"] = datetime.utcfromtimestamp(float(ts))
                    except Exception:
                        doc["timestamp"] = datetime.utcnow()
                else:
                    doc["timestamp"] = ts
            else:
                ts = doc["timestamp"]
                if isinstance(ts, (int, float)):
                    try:
                        doc["timestamp"] = datetime.utcfromtimestamp(float(ts))
                    except Exception:
                        doc["timestamp"] = datetime.utcnow()
                elif isinstance(ts, str):
                    try:
                        from dateutil import parser

                        doc["timestamp"] = parser.parse(ts)
                    except Exception:
                        doc["timestamp"] = datetime.utcnow()
            cleaned.append(doc)

        result = await self._collection.insert_many(cleaned)
        count = len(result.inserted_ids)
        logger.info("Stored %d flows in MongoDB.", count)
        return count

    async def list_flows(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[FlowFilters] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Return a paginated list of flows sorted by timestamp descending.

        Args:
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            filters: Optional filter criteria.

        Returns:
            A tuple of (list of flow dicts, total matching count).
        """
        query: Dict[str, Any] = {}
        if filters:
            if filters.src_ip:
                query["src_ip"] = filters.src_ip
            if filters.dst_ip:
                query["dst_ip"] = filters.dst_ip
            if filters.protocol:
                query["protocol"] = {"$regex": f"^{filters.protocol}$", "$options": "i"}
            if filters.session_id:
                query["capture_session_id"] = filters.session_id
            time_query: Dict[str, Any] = {}
            if filters.start_time:
                time_query["$gte"] = filters.start_time
            if filters.end_time:
                time_query["$lte"] = filters.end_time
            if time_query:
                query["timestamp"] = time_query

        total = await self._collection.count_documents(query)
        cursor = (
            self._collection.find(query, {"_id": 0})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        flows = await cursor.to_list(length=limit)
        return flows, total

    async def get_flow_stats(self) -> Dict[str, Any]:
        """Compute flow aggregation statistics.

        Returns a dict with:
        - ``protocol_distribution``: list of ``{protocol, count}`` dicts.
        - ``traffic_timeline``: list of ``{hour, count}`` dicts for the last
          24 hours.
        """
        # Protocol distribution
        protocol_pipeline = [
            {"$group": {"_id": "$protocol", "count": {"$sum": 1}}},
        ]
        protocol_cursor = self._collection.aggregate(protocol_pipeline)
        raw_protocol_dist = await protocol_cursor.to_list(length=100)
        protocol_map: Dict[str, int] = {}
        for p in raw_protocol_dist:
            proto = p.get("_id") or "Other"
            cnt = int(p.get("count") or 0)
            p_up = str(proto).upper()
            if p_up in ("HTTP", "HTTPS"):
                protocol_map[p_up] = protocol_map.get(p_up, 0) + cnt
            else:
                protocol_map[str(proto)] = protocol_map.get(str(proto), 0) + cnt
        protocol_distribution = [
            {"protocol": k, "count": v}
            for k, v in sorted(protocol_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Traffic timeline — last 24 hours grouped by hour
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        timeline_pipeline = [
            {"$match": {"timestamp": {"$gte": twenty_four_hours_ago}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:00:00Z",
                            "date": "$timestamp",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "hour": "$_id", "count": 1}},
        ]
        timeline_cursor = self._collection.aggregate(timeline_pipeline)
        traffic_timeline = await timeline_cursor.to_list(length=100)

        return {
            "protocol_distribution": protocol_distribution,
            "traffic_timeline": traffic_timeline,
        }

