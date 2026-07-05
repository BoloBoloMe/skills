"""pytest 配置: 每个测试前后重置 session, 确保隔离."""
import pytest
from browser_agent.session import reset_session as _reset


@pytest.fixture(autouse=True)
def fresh_session():
    _reset()
    yield
    _reset()
