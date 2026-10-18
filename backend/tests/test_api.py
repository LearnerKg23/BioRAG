import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "BioRAG"
    assert data["status"] == "operational"


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_corpus_stats():
    response = client.get("/api/papers/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_articles" in data
    assert "faiss_index_ready" in data


def test_benchmark_dataset_endpoint():
    response = client.get("/api/benchmark/dataset")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert data[0]["question_id"] == "bio_eval_001"


def test_benchmark_runs_list():
    response = client.get("/api/benchmark/runs")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "runs" in data


def test_chat_query():
    payload = {
        "query": "BRAF V600E melanoma targeted therapy",
        "k": 3,
        "mode": "hybrid_rrf"
    }
    response = client.post("/api/chat/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "answer" in data
    assert "citations" in data
    assert "confidence_score" in data
