from typing import List, Optional
from app.tools.base import MemoryTool
from app.tools.memory import ChromaMemoryTool, InMemoryFallbackTool


class MemoryService:
    """Service layer for inspecting client historical memory."""

    def __init__(self, memory_tool: Optional[MemoryTool] = None):
        self.memory_tool = memory_tool or ChromaMemoryTool()
        self.fallback_tool = InMemoryFallbackTool()

    async def get_client_memories(self, client_id: str, limit: int = 5) -> List[str]:
        try:
            mems = await self.memory_tool.retrieve_memories(client_id=client_id, limit=limit)
            if mems:
                return mems
        except Exception:
            pass
        return await self.fallback_tool.retrieve_memories(client_id=client_id, limit=limit)
