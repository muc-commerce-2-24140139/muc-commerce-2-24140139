"""第8天Flask项目API测试"""

import pytest
from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-key"
    with app.test_client() as client:
        yield client


def login(client, username="student", password="day07"):
    """辅助函数：登录获取session"""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True
    )


def test_health_endpoint(client):
    """测试1：/health 返回200和正确的服务信息"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["service"] == "day08-flask-upgrade"


def test_metrics_api_requires_login(client):
    """测试2：未登录访问 /api/metrics 应被重定向到登录页"""
    response = client.get("/api/metrics", follow_redirects=False)
    # 未登录时应该重定向到登录页
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_metrics_api_after_login(client):
    """测试3：登录后 /api/metrics 应返回正确的指标数据"""
    # 先登录
    login(client)

    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert "metrics" in data
    assert len(data["metrics"]) == 4

    # 验证指标结构
    expected_labels = ["总用户数", "流失用户", "总体流失率", "平均订单数"]
    actual_labels = [m["label"] for m in data["metrics"]]
    assert actual_labels == expected_labels

    # 验证每个指标包含必要字段
    for metric in data["metrics"]:
        assert "label" in metric
        assert "value" in metric
        assert "note" in metric
        assert isinstance(metric["value"], str)


def test_categories_api_filter(client):
    """测试4：/api/categories?category=Fashion 应返回筛选后的结果"""
    login(client)

    # 测试筛选 "Fashion"
    response = client.get("/api/categories?category=Fashion")
    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["category"] == "Fashion"
    assert "rows" in data
    assert isinstance(data["rows"], list)

    # 验证筛选后只有 Fashion 品类
    if data["rows"]:
        for row in data["rows"]:
            assert row["偏好品类"] == "Fashion"

    # 测试不传参数（默认"全部"）
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.get_json()
    assert data["category"] == "全部"
    # "全部"应该返回所有品类（5个）
    assert len(data["rows"]) == 5


def test_categories_api_requires_login(client):
    """测试5：未登录访问 /api/categories 应被拦截"""
    response = client.get("/api/categories", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_error_handler_400(client):
    """测试400错误处理器返回统一JSON结构"""
    # 先登录
    login(client)

    # 发送空问题触发400
    response = client.post(
        "/api/ask",
        json={"question": ""},  # 空问题
        content_type="application/json"
    )

    # 验证返回的是400错误
    assert response.status_code == 400
    data = response.get_json()

    # 验证错误结构（/api/ask 返回的是 answer 字段）
    assert data["ok"] is False
    assert "answer" in data
    assert data["answer"] == "请输入一个与项目数据有关的问题。"