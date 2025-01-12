import datetime
import math
from typing import Any
from unittest.mock import Mock

import pytest

from homework_05.scoring import get_scoring_key, get_score, get_interests
from homework_05.store import Store
from redis.exceptions import ConnectionError


@pytest.mark.parametrize(
    "case, score_kwargs, expected",
    [
        ("empty request", {}, 0),
        ("phone only", {"phone": "79213333333"}, 1.5),
        ("email only", {"email": "test@example.com"}, 1.5),
        (
            "birthday and gender is set",
            {"birthday": datetime.date(1999, 1, 1), "gender": 1},
            1.5,
        ),
        (
            "first_name and last_name is set",
            {"first_name": "John", "last_name": "Dow"},
            0.5,
        ),
        (
            "phone and first_name and last_name is set",
            {"phone": "79213333333", "first_name": "John", "last_name": "Dow"},
            2.0,
        ),
    ],
)
def test_scoring_get_score(case, score_kwargs, expected):
    store_mock = Mock(spec=Store)
    store_mock.cache_get = Mock(return_value=None)
    store_mock.cache_set = Mock(return_value=None)

    assert (
        get_score(store=store_mock, **score_kwargs) == expected
    ), f"Case '{case}' failed!"


def test_scoring_get_score_can_using_cache():
    key_kwargs = {
        "first_name": "a",
        "last_name": "b",
        "phone": "79175002040",
        "birthday": datetime.date(2000, 1, 1),
    }
    key = get_scoring_key(**key_kwargs)  # type: ignore
    expected_cached_value = 1500.0
    store_mock = Mock(spec=Store)
    store_mock.cache_get = Mock(
        side_effect=[None, str(expected_cached_value).encode("utf-8")]
    )
    store_mock.cache_set = Mock(return_value=None)
    scoring_kwargs = {"store": store_mock, "email": "stupnikov@otus.ru", "gender": 1}

    score = get_score(**(scoring_kwargs | key_kwargs))  # type: ignore
    assert score is not None

    # Check for store cache_get (returns None value) and cache_set was called as expected
    store_mock.cache_get.assert_called_once_with(key)
    store_mock.cache_set.assert_called_once_with(key, score, 60 * 60)

    store_mock.cache_get.reset_mock()
    store_mock.cache_set.reset_mock()

    # Check for store cache_get was called and get_score returns cached value.
    # cache_set should not be called in this case

    score = get_score(**(scoring_kwargs | key_kwargs))  # type: ignore
    assert math.isclose(score, expected_cached_value)

    store_mock.cache_get.assert_called_once_with(key)
    store_mock.cache_set.assert_not_called()


@pytest.mark.parametrize(
    "case, side_effect, expected",
    [
        ("No cached value. Returns empty list", None, []),
        ("Cached list", b'["testing"]', ["testing"]),
        ("Re rise error", ConnectionError("Test will pass!"), None),
    ],
)
def test_scoring_get_interests(case, side_effect: Any, expected):
    store_mock = Mock(spec=Store)
    store_mock.get = Mock(side_effect=[side_effect])
    if isinstance(side_effect, Exception):
        with pytest.raises(type(side_effect)):
            _ = get_interests(store_mock, "str")
    else:
        assert get_interests(store_mock, "str") == expected, f"Case '{case}' failed!"
