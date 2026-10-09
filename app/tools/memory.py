import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings
from app.logging_config import logger
from app.tools.base import MemoryTool


class InMemoryFallbackTool(MemoryTool):
    """Simple in-memory fallback vector memory for testing or environments where ChromaDB fails."""

    def __init__(self):
        self._memories: Dict[str, List[Dict[str, Any]]] = {}

    async def store_memory(self, client_id: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        if client_id not in self._memories:
            self._memories[client_id] = []
        self._memories[client_id].append({"summary": summary, "metadata": metadata or {}})
        return True

    async def retrieve_memories(self, client_id: str, query: str = "financial goals history risk", limit: int = 3) -> List[str]:
        client_mems = self._memories.get(client_id, [])
        return [m["summary"] for m in client_mems[-limit:]]


class ChromaMemoryTool(MemoryTool):
    """ChromaDB implementation of long-term memory with client_id isolation and fallback support."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_dir = persist_directory or "./data/chroma_db"
        self._collection = None
        self._initialized = False
        self._fallback = InMemoryFallbackTool()

    def _init_db(self):
        if self._initialized:
            return
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=self.persist_dir)

            emb_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            self._collection = client.get_or_create_collection(
                name="client_advisory_memory",
                embedding_function=emb_func
            )
            self._initialized = True
            logger.info("ChromaDB vector memory initialized successfully.", extra={"event": "memory_init"})
        except Exception as e:
            logger.warning(f"ChromaDB memory initialization note: {e}. Using resilient in-memory store.", extra={"event": "memory_init_note", "error": str(e)})
            self._initialized = False

    async def store_memory(self, client_id: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        if not settings.MEMORY_ENABLED:
            return False
        try:
            self._init_db()
            if not self._collection:
                return await self._fallback.store_memory(client_id, summary, metadata)

            import uuid
            doc_id = f"mem_{client_id}_{uuid.uuid4().hex[:8]}"
            meta = metadata or {}
            meta["client_id"] = client_id
            meta["type"] = "advisory_summary"

            self._collection.add(
                documents=[summary],
                metadatas=[meta],
                ids=[doc_id]
            )
            logger.info(f"Stored advisory memory for client {client_id}", extra={"event": "memory_store", "client_id": client_id})
            return True
        except Exception as e:
            logger.warning(f"ChromaDB store note: {e}. Falling back to in-memory store.", extra={"event": "memory_store_fallback", "client_id": client_id})
            return await self._fallback.store_memory(client_id, summary, metadata)

    async def retrieve_memories(self, client_id: str, query: str = "financial goals history risk", limit: int = 3) -> List[str]:
        if not settings.MEMORY_ENABLED:
            return []
        try:
            self._init_db()
            if not self._collection:
                return await self._fallback.retrieve_memories(client_id, query, limit)

            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where={"client_id": client_id}
            )

            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                logger.info(f"Retrieved {len(docs)} memories for client {client_id}", extra={"event": "memory_retrieve", "client_id": client_id})
                return docs
            return await self._fallback.retrieve_memories(client_id, query, limit)
        except Exception as e:
            logger.warning(f"ChromaDB retrieve note: {e}. Falling back to in-memory store.", extra={"event": "memory_retrieve_fallback", "client_id": client_id})
            return await self._fallback.retrieve_memories(client_id, query, limit)
