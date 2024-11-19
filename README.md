# AWS GPT Classifier

Решение на базе AWS API Gateway и AWS Lambda для обработки и классификации наименования номенклатуры по классам и атрибутам c помощью ChatGPT с использованием Redis в качестве хранилища данных (классификатор)

## Описание проекта

Этот проект реализует базовое API с использованием AWS Lambda, включающее три метода:

- **`GET /classify`**: Классифицирует переданное наименование номенклатуры на основе классификатора, хранящегося в Redis
- **`POST /pickAtt`**: Подбирает атрибуты для переданного наименования номенклатуры на основе классификатора, хранящегося в Redis
- **`POST /updateClassifier`**: Обновляет классификатор, сохраняя данные в Redis

## Структура проекта

Проект разделён на три отдельных Lambda-функции, каждая из которых обрабатывает свой эндпоинт:

- **`/src/classify.py`**: Обрабатывает запросы `GET /classify`.
- **`/src/pick_attributes.py`**: Обрабатывает запросы `POST /pickAtt`.
- **`/src/update_classifier.py`**: Обрабатывает запросы `POST /updateClassifier`.

## Структура данных в Redis

Для хранения классификатора и атрибутов используется база данных Redis (развернут в AWS рядом с Lambda-функциями). В этом разделе описана структура данных, которая используется для хранения информации в Redis.

### Ключи и значения

В Redis данные организованы в формате ключ-значение. Каждая запись классификатора хранится следующим образом:

1. **Ключи категорий**:
   - Ключи категорий хранятся в формате: `category:<название_категории>`.
   - Значение для каждой категории представляет собой JSON-объект с информацией о соответствующих атрибутах и весах.

2. **Примеры хранения категорий и атрибутов**:

## Структура данных в Redis

Для хранения классификатора и атрибутов используется база данных Redis. В этом разделе описана структура данных, которая используется для хранения информации в Redis.

### Ключи и значения

В Redis данные организованы в формате ключ-значение. Каждая запись классификатора хранится следующим образом:

1. **Ключи категорий**:
   - Ключи категорий хранятся в формате: `category:<название_категории>`.
   - Значение для каждой категории представляет собой JSON-объект с информацией о соответствующих атрибутах и весах.

2. **Примеры хранения категорий и атрибутов**:

#### Пример данных в Redis:

```plaintext
category:electronics
