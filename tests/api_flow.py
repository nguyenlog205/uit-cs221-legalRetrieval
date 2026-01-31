import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from main_api import app, agents

@pytest.mark.asyncio
async def test_chat_flow_general_intent():
    """Test luồng khi intent là 'general'"""
    # 1. Mock các Agent để không gọi API thật
    mock_classifier = AsyncMock()
    mock_classifier.classify.return_value = "general"
    
    mock_general_gen = MagicMock()
    mock_general_gen.generate_general.return_value = "Đây là câu trả lời general giả lập."

    # 2. Thay thế agents thật bằng mock
    with patch.dict(agents, {
        "classifier": mock_classifier,
        "general_gen": mock_general_gen
    }):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/chat", json={"query": "Chào bạn"})
            
    # 3. Kiểm tra kết quả "trượt" qua pipeline
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "general"
    assert "giả lập" in data["response"]
    mock_classifier.classify.assert_called_once_with("Chào bạn")

@pytest.mark.asyncio
async def test_chat_flow_specific_intent():
    """Test luồng RAG khi intent là 'specific'"""
    # 1. Mock Classifier, Retriever và SpecificGenerator
    mock_classifier = AsyncMock()
    mock_classifier.classify.return_value = "specific"

    mock_retriever = AsyncMock()
    # Giả lập trả về 1 document có metadata source
    mock_doc = MagicMock()
    mock_doc.metadata = {"source": "Luật Y Tế 2023"}
    mock_retriever.retrieve.return_value = [mock_doc]

    mock_specific_gen = AsyncMock()
    mock_specific_gen.generate_response.return_value = "Câu trả lời từ RAG giả lập."

    # 2. Thay thế agents
    with patch.dict(agents, {
        "classifier": mock_classifier,
        "retriever": mock_retriever,
        "specific_gen": mock_specific_gen
    }):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/chat", json={"query": "Thủ tục khám bệnh là gì?"})

    # 3. Kiểm tra
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "specific"
    assert "Luật Y Tế 2023" in data["source_documents"]
    assert "RAG giả lập" in data["response"]
    
    # Đảm bảo retriever đã được gọi
    mock_retriever.retrieve.assert_called_once()

@pytest.mark.asyncio
async def test_health_check():
    """Test endpoint health đơn giản"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"