#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Milvus vector database utility module

Provides vector database connection, collection management, vector insertion and retrieval functions
"""

from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from contextlib import asynccontextmanager

from .config import get_config
from .logger import get_logger
from .exceptions import DatabaseError, InvalidParameterError, ResourceNotFoundError

logger = get_logger(__name__)

try:
    from pymilvus import (
        connections,
        utility,
        Collection,
        CollectionSchema,
        FieldSchema,
        DataType,
        MilvusException,
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    # Provide placeholders so class definitions pass syntax check (instantiation will raise DatabaseError in __init__)
    connections = None  # type: ignore
    utility = None  # type: ignore
    Collection = None  # type: ignore
    CollectionSchema = None  # type: ignore
    FieldSchema = None  # type: ignore
    DataType = None  # type: ignore
    MilvusException = Exception  # type: ignore


# ==================== Data type mapping ====================
if MILVUS_AVAILABLE:
    _MILVUS_TYPE_MAP = {
        "BOOL": DataType.BOOL,
        "INT8": DataType.INT8,
        "INT16": DataType.INT16,
        "INT32": DataType.INT32,
        "INT64": DataType.INT64,
        "FLOAT": DataType.FLOAT,
        "DOUBLE": DataType.DOUBLE,
        "VARCHAR": DataType.VARCHAR,
        "JSON": DataType.JSON,
        "BINARY_VECTOR": DataType.BINARY_VECTOR,
        "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
    }
else:
    _MILVUS_TYPE_MAP: Dict[str, Any] = {}


class MilvusClient:
    """Milvus vector database client"""

    def __init__(self, alias: Optional[str] = None):
        """
        Initialize Milvus client

        Args:
            alias: Connection alias, default is MILVUS_ALIAS from configuration
        """
        if not MILVUS_AVAILABLE:
            logger.warning("pymilvus not installed, vector database functionality unavailable")
            raise DatabaseError("pymilvus not installed, please run: pip install pymilvus>=2.3.0")

        config = get_config()
        self.alias = alias or config.MILVUS_ALIAS
        self.host = config.MILVUS_HOST
        self.port = config.MILVUS_PORT
        self.user = config.MILVUS_USER
        self.password = config.MILVUS_PASSWORD
        self.connect_timeout = config.MILVUS_CONNECT_TIMEOUT

        self._connected = False
        self._default_dim = config.MILVUS_DEFAULT_DIM
        self._default_metric = config.MILVUS_DEFAULT_METRIC
        self._default_index = config.MILVUS_DEFAULT_INDEX

    def connect(self) -> None:
        """Establish Milvus connection"""
        if self._connected:
            return

        try:
            connect_params = {
                "host": self.host,
                "port": self.port,
                "timeout": self.connect_timeout,
            }

            if self.user and self.password:
                connect_params["user"] = self.user
                connect_params["password"] = self.password

            connections.connect(alias=self.alias, **connect_params)
            self._connected = True
            logger.info(f"✅ Milvus connection successful: {self.host}:{self.port}")
        except MilvusException as e:
            raise DatabaseError(f"Milvus connection failed: {str(e)}") from e

    def disconnect(self) -> None:
        """Close Milvus connection"""
        if self._connected:
            try:
                connections.disconnect(self.alias)
                self._connected = False
                logger.info("✅ Milvus connection closed")
            except MilvusException as e:
                logger.warning(f"Milvus close connection exception: {e}")

    def check_health(self) -> bool:
        """
        Check Milvus health status

        Returns:
            bool: Health status
        """
        try:
            if not self._connected:
                self.connect()
            version = utility.get_server_version()
            logger.info(f"Milvus service normal, version: {version}")
            return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False

    # ==================== Collection management ====================

    def has_collection(self, collection_name: str) -> bool:
        """
        Check if collection exists

        Args:
            collection_name: Collection name

        Returns:
            bool: Whether exists
        """
        if not self._connected:
            self.connect()
        return utility.has_collection(collection_name, using=self.alias)

    def create_collection(
        self,
        collection_name: str,
        fields: List[Dict[str, Any]],
        description: str = "",
        auto_id: bool = False,
        enable_dynamic_field: bool = True,
    ) -> Collection:
        """
        Create vector collection

        Args:
            collection_name: Collection name
            fields: Field definition list, each field includes: name, type, params, description, etc.
            description: Collection description
            auto_id: Whether to auto-generate primary key
            enable_dynamic_field: Whether to enable dynamic field

        Returns:
            Collection: Created collection object

        Example:
            fields = [
                {"name": "id", "type": "INT64", "is_primary": True, "auto_id": False},
                {"name": "vector", "type": "FLOAT_VECTOR", "params": {"dim": 1536}},
                {"name": "content", "type": "VARCHAR", "params": {"max_length": 65535}},
                {"name": "metadata", "type": "JSON"},
            ]
            client.create_collection("my_collection", fields)
        """
        if self.has_collection(collection_name):
            logger.warning(f"Collection already exists: {collection_name}")
            return Collection(collection_name, using=self.alias)

        schema_fields = []
        for field in fields:
            field_type = _MILVUS_TYPE_MAP.get(field["type"].upper())
            if not field_type:
                raise InvalidParameterError(f"Unsupported field type: {field['type']}")

            field_params = field.get("params", {})
            if field_type == DataType.FLOAT_VECTOR and "dim" not in field_params:
                field_params["dim"] = self._default_dim

            schema_fields.append(
                FieldSchema(
                    name=field["name"],
                    dtype=field_type,
                    description=field.get("description", ""),
                    is_primary=field.get("is_primary", False),
                    auto_id=field.get("auto_id", False),
                    **field_params,
                )
            )

        schema = CollectionSchema(
            fields=schema_fields,
            description=description,
            enable_dynamic_field=enable_dynamic_field,
        )

        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.alias,
            auto_id=auto_id,
        )

        logger.info(f"✅ Collection created successfully: {collection_name}")
        return collection

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get collection object

        Args:
            collection_name: Collection name

        Returns:
            Collection: Collection object
        """
        if not self.has_collection(collection_name):
            raise ResourceNotFoundError(f"Collection does not exist: {collection_name}")
        return Collection(collection_name, using=self.alias)

    def drop_collection(self, collection_name: str) -> None:
        """
        Delete collection

        Args:
            collection_name: Collection name
        """
        if self.has_collection(collection_name):
            utility.drop_collection(collection_name, using=self.alias)
            logger.info(f"✅ Collection deleted successfully: {collection_name}")

    def list_collections(self) -> List[str]:
        """
        List all collections

        Returns:
            List[str]: Collection name list
        """
        if not self._connected:
            self.connect()
        return utility.list_collections(using=self.alias)

    # ==================== Index management ====================

    def create_index(
        self,
        collection_name: str,
        field_name: str,
        index_type: Optional[str] = None,
        metric_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create vector index

        Args:
            collection_name: Collection name
            field_name: Vector field name
            index_type: Index type (IVF_FLAT, IVF_SQ8, IVF_PQ, HNSW, FLAT, etc.)
            metric_type: Distance metric type (COSINE, L2, IP)
            params: Index parameters (e.g.: nlist, M, efConstruction, etc.)
        """
        collection = self.get_collection(collection_name)

        index_type = index_type or self._default_index
        metric_type = metric_type or self._default_metric
        params = params or {}

        # Set default parameters based on index type
        if index_type == "IVF_FLAT" and "nlist" not in params:
            params["nlist"] = 1024
        elif index_type == "HNSW" and "M" not in params:
            params["M"] = 16
            params["efConstruction"] = 256

        index_params = {
            "metric_type": metric_type,
            "index_type": index_type,
            "params": params,
        }

        collection.create_index(field_name, index_params)
        logger.info(f"✅ Index created successfully: {collection_name}.{field_name} ({index_type})")

    def load_collection(self, collection_name: str) -> None:
        """
        Load collection into memory (must be called before query)

        Args:
            collection_name: Collection name
        """
        collection = self.get_collection(collection_name)
        collection.load()
        logger.debug(f"Collection loaded: {collection_name}")

    def release_collection(self, collection_name: str) -> None:
        """
        Release collection from memory

        Args:
            collection_name: Collection name
        """
        collection = self.get_collection(collection_name)
        collection.release()
        logger.debug(f"Collection released: {collection_name}")

    # ==================== Data operations ====================

    def insert(self, collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert vector data

        Args:
            collection_name: Collection name
            data: Data list, each item is field name to value mapping

        Returns:
            Dict: Insert result information

        Example:
            data = [
                {"id": 1, "vector": [0.1, 0.2, ...], "content": "Test text", "metadata": {"source": "doc1"}},
                {"id": 2, "vector": [0.3, 0.4, ...], "content": "Test text2", "metadata": {"source": "doc2"}},
            ]
            client.insert("my_collection", data)
        """
        collection = self.get_collection(collection_name)

        # Convert to list format grouped by field (required by Milvus API)
        field_names = collection.schema.names
        insert_data = []
        for field in collection.schema.fields:
            if field.auto_id:
                continue
            field_values = [item.get(field.name) for item in data]
            insert_data.append(field_values)

        result = collection.insert(insert_data)

        logger.info(f"✅ Data inserted successfully: {collection_name}, Count: {len(data)}")
        return {
            "insert_count": result.insert_count,
            "primary_keys": result.primary_keys,
        }

    def delete(self, collection_name: str, expr: str) -> int:
        """
        Delete data by expression

        Args:
            collection_name: Collection name
            expr: Delete expression, e.g. "id in [1, 2, 3]"

        Returns:
            int: Deleted count
        """
        collection = self.get_collection(collection_name)
        result = collection.delete(expr)
        logger.info(f"✅ Data deleted successfully: {collection_name}, Count: {result.delete_count}")
        return result.delete_count

    def search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        vector_field: str = "vector",
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        limit: int = 10,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Vector similarity search

        Args:
            collection_name: Collection name
            query_vectors: Query vector list
            vector_field: Vector field name
            filter_expr: Filter expression
            output_fields: Return field list
            limit: Result count
            params: Search parameters (e.g.: ef, nprobe, etc.)

        Returns:
            List[List[Dict]]: Search results, each query corresponds to a result list,
            each result contains id, score, and fields specified by output_fields

        Example:
            results = client.search(
                "my_collection",
                [[0.1, 0.2, ...]],
                filter_expr="status == 'active'",
                output_fields=["id", "content", "metadata"],
                limit=5,
            )
        """
        collection = self.get_collection(collection_name)

        # Ensure collection is loaded
        try:
            collection.load()
        except MilvusException:
            # May already be loaded
            pass

        params = params or {"nprobe": 16}

        results = collection.search(
            data=query_vectors,
            anns_field=vector_field,
            param=params,
            limit=limit,
            expr=filter_expr,
            output_fields=output_fields or [],
        )

        # Convert to more friendly format
        formatted_results = []
        for hits in results:
            hit_list = []
            for hit in hits:
                result_item = {
                    "id": hit.id,
                    "score": hit.score,
                }
                if output_fields:
                    result_item.update({field: hit.entity.get(field) for field in output_fields})
                hit_list.append(result_item)
            formatted_results.append(hit_list)

        return formatted_results

    def query(
        self,
        collection_name: str,
        expr: str,
        output_fields: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scalar query (based on non-vector fields)

        Args:
            collection_name: Collection name
            expr: Query expression, e.g. "id > 100"
            output_fields: Return field list
            limit: Result count limit

        Returns:
            List[Dict]: Query result list
        """
        collection = self.get_collection(collection_name)

        results = collection.query(
            expr=expr,
            output_fields=output_fields or [],
            limit=limit,
        )

        return results

    def upsert(self, collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update or insert data (Upsert)

        Args:
            collection_name: Collection name
            data: Data list

        Returns:
            Dict: Operation result
        """
        # Milvus currently has no native upsert, here we delete first then insert
        # Note: Requires primary key field
        collection = self.get_collection(collection_name)
        primary_key = None

        for field in collection.schema.fields:
            if field.is_primary:
                primary_key = field.name
                break

        if not primary_key:
            raise InvalidParameterError("Upsert requires collection to have a primary key field")

        # Extract all primary keys and delete old data
        ids = [item[primary_key] for item in data]
        if ids:
            id_str = ", ".join(str(i) for i in ids)
            self.delete(collection_name, f"{primary_key} in [{id_str}]")

        # Insert new data
        return self.insert(collection_name, data)


# ==================== Global instance ====================
_global_milvus_client: Optional[MilvusClient] = None


def get_milvus_client() -> MilvusClient:
    """
    Get global Milvus client instance (singleton)

    Returns:
        MilvusClient: Client instance
    """
    global _global_milvus_client
    if _global_milvus_client is None:
        _global_milvus_client = MilvusClient()
    return _global_milvus_client


def check_milvus_health() -> bool:
    """
    Check Milvus health status (convenience function)

    Returns:
        bool: Health status
    """
    if not MILVUS_AVAILABLE:
        return False
    try:
        client = MilvusClient()
        return client.check_health()
    except Exception:
        return False


@asynccontextmanager
async def milvus_context():
    """
    Milvus async context manager

    Usage:
        async with milvus_context() as client:
            results = client.search(...)
    """
    client = get_milvus_client()
    try:
        client.connect()
        yield client
    finally:
        # Keep connection for reuse, do not close proactively
        pass
