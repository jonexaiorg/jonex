#!/usr/bin/python3



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

    connections = None
    utility = None
    Collection = None
    CollectionSchema = None
    FieldSchema = None
    DataType = None
    MilvusException = Exception



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


    def __init__(self, alias: Optional[str] = None):

        if not MILVUS_AVAILABLE:
            logger.warning("pymilvus is not installed; vector database features are unavailable")
            raise DatabaseError("pymilvus 未安装，请执行: pip install pymilvus>=2.3.0")

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
            logger.info(f"✅ Connected to Milvus: {self.host}:{self.port}")
        except MilvusException as e:
            raise DatabaseError(f"Milvus 连接失败: {str(e)}") from e

    def disconnect(self) -> None:

        if self._connected:
            try:
                connections.disconnect(self.alias)
                self._connected = False
                logger.info("✅ Milvus connection closed")
            except MilvusException as e:
                logger.warning(f"Error closing Milvus connection: {e}")

    def check_health(self) -> bool:

        try:
            if not self._connected:
                self.connect()
            version = utility.get_server_version()
            logger.info(f"Milvus service is healthy, version: {version}")
            return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False



    def has_collection(self, collection_name: str) -> bool:

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

        if self.has_collection(collection_name):
            logger.warning(f"Collection already exists: {collection_name}")
            return Collection(collection_name, using=self.alias)

        schema_fields = []
        for field in fields:
            field_type = _MILVUS_TYPE_MAP.get(field["type"].upper())
            if not field_type:
                raise InvalidParameterError(f"不支持的字段类型: {field['type']}")

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

        logger.info(f"✅ Collection created: {collection_name}")
        return collection

    def get_collection(self, collection_name: str) -> Collection:

        if not self.has_collection(collection_name):
            raise ResourceNotFoundError(f"集合不存在: {collection_name}")
        return Collection(collection_name, using=self.alias)

    def drop_collection(self, collection_name: str) -> None:

        if self.has_collection(collection_name):
            utility.drop_collection(collection_name, using=self.alias)
            logger.info(f"✅ Collection dropped: {collection_name}")

    def list_collections(self) -> List[str]:

        if not self._connected:
            self.connect()
        return utility.list_collections(using=self.alias)



    def create_index(
        self,
        collection_name: str,
        field_name: str,
        index_type: Optional[str] = None,
        metric_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:

        collection = self.get_collection(collection_name)

        index_type = index_type or self._default_index
        metric_type = metric_type or self._default_metric
        params = params or {}


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
        logger.info(f"✅ Index created: {collection_name}.{field_name} ({index_type})")

    def load_collection(self, collection_name: str) -> None:

        collection = self.get_collection(collection_name)
        collection.load()
        logger.debug(f"Collection loaded: {collection_name}")

    def release_collection(self, collection_name: str) -> None:

        collection = self.get_collection(collection_name)
        collection.release()
        logger.debug(f"Collection released: {collection_name}")



    def insert(self, collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:

        collection = self.get_collection(collection_name)


        field_names = collection.schema.names
        insert_data = []
        for field in collection.schema.fields:
            if field.auto_id:
                continue
            field_values = [item.get(field.name) for item in data]
            insert_data.append(field_values)

        result = collection.insert(insert_data)

        logger.info(f"✅ Data inserted: {collection_name}, count: {len(data)}")
        return {
            "insert_count": result.insert_count,
            "primary_keys": result.primary_keys,
        }

    def delete(self, collection_name: str, expr: str) -> int:

        collection = self.get_collection(collection_name)
        result = collection.delete(expr)
        logger.info(f"✅ Data deleted: {collection_name}, count: {result.delete_count}")
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

        collection = self.get_collection(collection_name)


        try:
            collection.load()
        except MilvusException:

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

        collection = self.get_collection(collection_name)

        results = collection.query(
            expr=expr,
            output_fields=output_fields or [],
            limit=limit,
        )

        return results

    def upsert(self, collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:



        collection = self.get_collection(collection_name)
        primary_key = None

        for field in collection.schema.fields:
            if field.is_primary:
                primary_key = field.name
                break

        if not primary_key:
            raise InvalidParameterError("Upsert 需要集合有主键字段")


        ids = [item[primary_key] for item in data]
        if ids:
            id_str = ", ".join(str(i) for i in ids)
            self.delete(collection_name, f"{primary_key} in [{id_str}]")


        return self.insert(collection_name, data)



_global_milvus_client: Optional[MilvusClient] = None


def get_milvus_client() -> MilvusClient:

    global _global_milvus_client
    if _global_milvus_client is None:
        _global_milvus_client = MilvusClient()
    return _global_milvus_client


def check_milvus_health() -> bool:

    if not MILVUS_AVAILABLE:
        return False
    try:
        client = MilvusClient()
        return client.check_health()
    except Exception:
        return False


@asynccontextmanager
async def milvus_context():

    client = get_milvus_client()
    try:
        client.connect()
        yield client
    finally:

        pass
