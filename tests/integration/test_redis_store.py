import datetime

import pytest
from testcontainers.redis import RedisContainer

from homework_05.scoring import get_scoring_key, get_score
from homework_05.store import RedisStore
from redis.exceptions import ConnectionError


@pytest.fixture(scope="function")
def redis_store():
    with RedisContainer() as redis_container:
        yield RedisStore(
            redis_container.get_container_host_ip(),
            redis_container.get_exposed_port(redis_container.port),
            redis_container.password,
        )


@pytest.mark.skip_integration_test_if_not_enabled()
def test_store_can_write_and_read_values(redis_store):
    key = "str_key"
    value = "value"
    assert redis_store.cache_get(key) is None
    redis_store.cache_set(key, value, 3600)
    assert redis_store.get(key).decode("utf-8") == value


@pytest.mark.skip_integration_test_if_not_enabled()
def test_scoring_get_score_can_use_store(redis_store):
    key_kwargs = {
        "first_name": "a",
        "last_name": "b",
        "phone": "79175002040",
        "birthday": datetime.date(2000, 1, 1),
    }

    scoring_kwargs = {"store": redis_store, "email": "stupnikov@otus.ru", "gender": 1}
    key = get_scoring_key(**key_kwargs)  # type: ignore
    assert redis_store.cache_get(key) is None, f"В кэше не должно быть значения {key}"
    score = get_score(**(scoring_kwargs | key_kwargs))  # type: ignore

    assert (
        float(redis_store.get(key)) == score
    ), f"В кэше должно быть значения {key}={score}"


@pytest.mark.skip_integration_test_if_not_enabled()
def test_scoring_get_score_can_work_if_redis_is_unavailable():
    redis_store = RedisStore("non_existent_host")
    key_kwargs = {
        "first_name": "a",
        "last_name": "b",
        "phone": "79175002040",
        "birthday": datetime.date(2000, 1, 1),
    }

    scoring_kwargs = {"store": redis_store, "email": "stupnikov@otus.ru", "gender": 1}
    key = get_scoring_key(**key_kwargs)  # type: ignore
    assert redis_store.cache_get(key) is None, f"В кэше не должно быть значения {key}"
    score = get_score(**(scoring_kwargs | key_kwargs))  # type: ignore

    assert score > 0
    with pytest.raises(ConnectionError):
        redis_store.get(key)
