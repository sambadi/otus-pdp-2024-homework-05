import abc
import logging
from typing import Any

from redis.backoff import ExponentialBackoff
from redis.retry import Retry
import redis
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

logger = logging.getLogger()


class Store(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str) -> Any:
        """
        Get value from KV-store. If store is unavailable raises an error
        :param key: String key to search
        :return: Found value
        """

    @abc.abstractmethod
    def cache_get(self, key: str) -> Any:
        """
        Get cached value from store.
        :param key: String key to search
        :return: Found value or None
        """

    @abc.abstractmethod
    def cache_set(self, key: str, value: Any, ttl: int = 60):
        """
        Get cached value from store. If no value found or store is unavailable raises an error
        :param key: String key to search
        :param value: Value to store at cache
        :param ttl: Time to life of stored value
        :return: None
        """


class RedisStore(Store):
    def __init__(
        self,
        host: str,
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
    ):
        retry = Retry(ExponentialBackoff(), 3)
        self.__redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            retry=retry,
            retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError],
            socket_connect_timeout=10,
            retry_on_timeout=True,
        )

    def get(self, key: str) -> bytes | None:
        try:
            return self.__redis.get(key)
        except BusyLoadingError as e:
            logger.error(e)
            raise BusyLoadingError(f"Redis server is too busy. Error: {e}") from e
        except ConnectionError as e:
            logger.error(e)
            raise ConnectionError(f"Redis server is unreachable. Error: {e}") from e
        except TimeoutError as e:
            logger.error(e)
            raise TimeoutError(
                f"Redis server connection is timed out. Error: {e}"
            ) from e

    def cache_get(self, key: str) -> bytes | None:
        try:
            return self.__redis.get(key)
        except Exception as e:
            logger.error(f"Error on get cached value for key '{key}': {e}")
            return None

    def cache_set(self, key: str, value: Any, ttl: int = 60):
        try:
            self.__redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Error on preserve cached value for key '{key}': {e}")
