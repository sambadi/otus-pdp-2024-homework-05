# Пятое ДЗ в рамках обучения на курсах Otus

На реализованный ранее проект, реализующий HTTP API сервиса скоринга, написаны unit и интеграционные тесты.

## Запуск проекта

Для запуска проекта достаточно:

- склонировать репозиторий;
- установить Python 3.12 любым доступным способом;
- установить [poetry](https://python-poetry.org/docs/#installation)
- установить зависимости выполнив команду

```shell
 poetry install
```

- запуск на выполнение

```shell
  poetry run python -m homework_05
```

## Пример запроса

```
$ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
```

```
{"code": 200, "response": {"score": 5.0}}
```

# Использование Makefile

Для удобства использования в проект добавлена поддержка make actions. Доступны следующий команды:

- `make install` - установка зависимостей;
- `make run` - запуск приложения;
- `make test` - запуск тестов с покрытием;
- `make lint` - запуск проверки кода;
- `make run-with-docker` - запуск приложения с использованием docker;

