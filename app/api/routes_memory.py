from fastapi import APIRouter
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["Memory"])
memory_service = MemoryService()


@router.get("/{client_id}")
async def get_client_memory(client_id: str, limit: int = 5):
    """Retrieve long-term memory summaries for a specific client."""
    memories = await memory_service.get_client_memories(client_id, limit=limit)
    return {
        "client_id": client_id,
        "count": len(memories),
        "memories": memories
    }
