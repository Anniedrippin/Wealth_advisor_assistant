import pytest
from app.tools.crm import MockCRMTool, HTTPCRMTool
from app.tools.memory import InMemoryFallbackTool


@pytest.mark.asyncio
async def test_mock_crm_tool():
    tool = MockCRMTool()
    client = await tool.get_client("C1001")
    assert client is not None
    assert client.client_id == "C1001"
    assert client.name == "Sarah Connor"


@pytest.mark.asyncio
async def test_mock_crm_tool_not_found():
    tool = MockCRMTool()
    client = await tool.get_client("NON_EXISTENT")
    assert client is None


@pytest.mark.asyncio
async def test_memory_isolation_by_client_id():
    mem_tool = InMemoryFallbackTool()
    
    # Store memories for Client A
    await mem_tool.store_memory("CLIENT_A", "Client A prefers low risk index funds.")
    
    # Store memories for Client B
    await mem_tool.store_memory("CLIENT_B", "Client B has high travel expenses.")
    
    # Retrieve memories for Client A
    a_mems = await mem_tool.retrieve_memories("CLIENT_A")
    assert len(a_mems) == 1
    assert "Client A" in a_mems[0]
    assert "Client B" not in a_mems[0]

    # Retrieve memories for Client B
    b_mems = await mem_tool.retrieve_memories("CLIENT_B")
    assert len(b_mems) == 1
    assert "Client B" in b_mems[0]
    assert "Client A" not in b_mems[0]
