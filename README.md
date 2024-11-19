# AWS GPT Classifier

Решение на базе AWS API Gateway и AWS Lambda для обработки и классификации наименования номенклатуры по классам и атрибутам c помощью ChatGPT с использованием Redis в качестве хранилища данных (классификатор)

## Описание проекта

Этот проект реализует REST API с использованием AWS Lambda, включающее три метода:

- **`GET /classify`**: Классифицирует переданное наименование номенклатуры на основе классификатора, хранящегося в Redis
- **`POST /pickAtt`**: Подбирает атрибуты для переданного наименования номенклатуры на основе классификатора, хранящегося в Redis
- **`POST /updateClassifier`**: Обновляет классификатор, сохраняя данные в Redis

## Структура проекта

Проект разделён на три отдельных Lambda-функции, каждая из которых обрабатывает свой эндпоинт:

- **[classify.py](/src/classify.py)**: Обрабатывает запросы `GET /classify`
- **[pick_attributes.py](/src/pick_attributes.py)**: Обрабатывает запросы `POST /pickAtt`
- **[update_classifier.py](/src/update_classifier.py)**: Обрабатывает запросы `POST /updateClassifier`

## Структура данных в Redis

Для хранения классификатора (наименования, коды классов и наборы атрибутов) используется база данных Redis (развернут в AWS рядом с Lambda-функциями)

### Ключи и значения

В Redis данные организованы в формате ключ-значение. Каждая запись классификатора хранится следующим образом:

1. **Ключи классов**:
   - Ключи классов хранятся в формате:
     - `000000000000001`
     - `000000000000011`
     - `000000000000012`
     - `000000000000121`
     - и тд (таким образом реализована иерархия)
2. **Значения классов**:
   - Значение для каждого класса представляет собой JSON-объект с информацией о соответствующих наименованиях и атрибутах

2. **Примеры хранения категорий и атрибутов**:

#### Пример данных в Redis:
**Ключ**: `000000057030105`

**Значение**:
```json
{
   "code":"000000057030105",
   "name":"Хроматографы, анализаторы состава веществ",
   "attributes":[
      {
         "attribute_name":"Вид продукции",
         "attribute_type":"Текст",
         "attribute_example":"Хроматограф"
      },
      {
         "attribute_name":"Тип",
         "attribute_type":"Текст",
         "attribute_example":"газовый"
      },
      {
         "attribute_name":"Назначение",
         "attribute_type":"Текст",
         "attribute_example":"для определения содержания кислорода и кислородсодержащих соединений"
      },
      {
         "attribute_name":"Диапазон рабочих температур, C",
         "attribute_type":"Текст",
         "attribute_example":"5C...400C"
      },
      {
         "attribute_name":"Диапазон входного давления, МПа",
         "attribute_type":"Текст",
         "attribute_example":"0,36-0,44"
      },
      {
         "attribute_name":"Комплектация",
         "attribute_type":"Текст",
         "attribute_example":"с переключающимися колонками и контроллером"
      },
      {
         "attribute_name":"Опросный лист",
         "attribute_type":"Текст",
         "attribute_example":"2020-013-Р-1-0-ТХ.ОЛ46"
      }
   ]
}
```
## Документация

- [API Документация](docs/aws-gpt-classifier-api.yaml)

## Примеры использования

**`GET /classify`**

**response**:
```bash
curl -G "your-url-endpoint/prod/classify" \
  --data-urlencode "itemName=Шпилька 2-1-М36-6gx200.35 ОСТ 26-2040-96" \
  -H "Accept: application/json" \
  -H "x-api-key: <API_KEY>" \
  | jq
```
**request**:
```json
{
  "input_item_name": "Шпилька 2-1-М36-6gx200.35 ОСТ 26-2040-96",
  "result": [
    {
      "class_name": "ИЗДЕЛИЯ КРЕПЕЖНЫЕ ОБЩЕМАШИНОСТРОИТЕЛЬНОГО ПРИМЕНЕНИЯ",
      "class_code": "000000000000006"
    },
    {
      "class_name": "Шпильки",
      "class_code": "000000000000616"
    },
    {
      "class_name": "Шпильки, обозначаемые по ГОСТ",
      "class_code": "000000000061601"
    },
    {
      "class_name": "Шпильки по ОСТ 26-2040",
      "class_code": "000000006160103"
    }
  ]
}
```
**`POST /pickAtt`**

**request**:
```bash
curl -X POST your-url-endpoint/prod/pickAtt \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d '{"item_name": "Труба тип 3-820x9-К52 ГОСТ 20295-85",
	   "final_class_name": "Трубы стальные сварные для магистральных газонефтепроводов",
	   "final_class_code": "000000004010202"}' \
  | jq
```

**response**:
```json
{
  "input_item_name": "Труба тип 3-820x9-К52 ГОСТ 20295-85",
  "input_final_class_name": "Трубы стальные сварные для магистральных газонефтепроводов",
  "input_final_class_code": "000000004010202",
  "result": [
    {
      "attribute_name": "Вид продукции",
      "attribute_type": "Текст",
      "attribute_example": "Труба стальная",
      "attribute_decision": "Труба"
    },
    {
      "attribute_name": "Тип трубы",
      "attribute_type": "Текст",
      "attribute_example": "тип 1",
      "attribute_decision": "тип 3"
    },
    {
      "attribute_name": "Термообработка",
      "attribute_type": "Текст",
      "attribute_example": "У",
      "attribute_decision": null
    },
    {
      "attribute_name": "Диаметр, мм",
      "attribute_type": "Число",
      "attribute_example": "820",
      "attribute_decision": 820
    },
    {
      "attribute_name": "Толщина стенки, мм",
      "attribute_type": "Число",
      "attribute_example": "10",
      "attribute_decision": 9
    },
    {
      "attribute_name": "Класс прочности",
      "attribute_type": "Текст",
      "attribute_example": "К52",
      "attribute_decision": "К52"
    },
    {
      "attribute_name": "Марка металла или сплава",
      "attribute_type": "Текст",
      "attribute_example": "17Г1С",
      "attribute_decision": null
    },
    {
      "attribute_name": "Стандарт технических требований",
      "attribute_type": "Текст",
      "attribute_example": "ГОСТ 20295-85",
      "attribute_decision": "ГОСТ 20295-85"
    },
    {
      "attribute_name": "Тип покрытия",
      "attribute_type": "Текст",
      "attribute_example": "без покрытия",
      "attribute_decision": null
    }
  ]
}
```
**`POST /pickAtt`**

**request**:
```bash
curl -X POST "your-url-endpoint/prod/updateClassifier" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d @data.json | jq
```
**data.json**:
```json
[
   {
      "key":"000000000000005",
      "data":{
         "code":"000000000000005",
         "name":"ЭЛЕКТРОЭНЕРГИЯ ТЕПЛОЭНЕРГИЯ УГОЛЬ АЗОТ ВОДОРОД ВОДА ПРИРОДНЫЙ ГАЗ",
         "attributes":null
      }
   },
   {
      "key":"000000000000703",
      "data":{
         "code":"000000000000703",
         "name":"Электролиты щелочные и кислотные",
         "attributes":[
            {
               "attribute_name":"Вид продукции",
               "attribute_type":"Текст",
               "attribute_example":"Электролит"
            },
            {
               "attribute_name":"Тип",
               "attribute_type":"Текст",
               "attribute_example":"кислотный"
            },
            {
               "attribute_name":"Плотность, г/м3",
               "attribute_type":"Число",
               "attribute_example":1.27
            },
            {
               "attribute_name":"Объем, л",
               "attribute_type":"Число",
               "attribute_example":5
            }
         ]
      }
   }
]
```

**response**:
```json
{
  "result": "OK"
}
```
