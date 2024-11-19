import json
import redis
import openai
import os
import re
import logging
from redis.commands.json.path import Path

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info("----> Получение данных из POST-запроса")
        
        # Извлечение данных из тела POST-запроса
        body = json.loads(event['body'])
        item_name = body.get('item_name')
        final_class_name = body.get('final_class_name')
        final_class_code = body.get('final_class_code')
        
        logger.info(f"----> Параметры запроса: item_name={item_name}, final_class_name={final_class_name}, final_class_code={final_class_code}")
        
        # Проверка, что параметры не null
        if not item_name or not final_class_name or not final_class_code:
            logger.error("----> Отсутствуют обязательные параметры item_name или final_class_name или final_class_code")
            return {
                'statusCode': 400,
                'body': json.dumps('item_name, final_class_name и final_class_code обязательны')
            }
        
        # Чтение переменных окружения для подключения
        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        OPENAI_TOKEN = os.getenv('OPENAI_TOKEN', 'empty')
        MODEL = "gpt-4o"
        TEMPERATURE = 0

        # Настройки API OpenAI (ChatGPT)
        openai.api_key = OPENAI_TOKEN

        # Настройка подключения к Redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        # Проверка соединения с Redis
        r.ping()

        # Извлечение данных из Redis по коду класса
        logger.info(f"----> Попытка извлечь данные из Redis для кода класса: {final_class_code}")
        redis_data = r.json().get(final_class_code, Path.root_path())
        
        if not redis_data:
            logger.error(f"----> Данные не найдены в Redis для кода класса: {final_class_code}")
            return {
                'statusCode': 404,
                'body': json.dumps(f"Код класса {final_class_code} не найден в Redis", ensure_ascii=False)
            }
        
        attributes = redis_data.get('attributes')
        
        # Проверка на null (attributes)
        if attributes is None:
            logger.error(f"Attributes не найдены в Redis. Код класса {final_class_code}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Attributes не найдены в Redis. Код класса {final_class_code}", ensure_ascii=False)
            }

        # Добавление ключа 'attribute_decision' со значением null
        for attribute in attributes:
            attribute['attribute_decision'] = None

        # Запрос к ChatGPT для заполнения attribute_decision
        logger.info("----> Формирование запроса к ChatGPT")
        prompt = f"""Условия: на вход поступает номенклатурная позиция и json схема аттрибутов, где attribute_name - имя аттрибута, attribute_type - тип данных, attribute_example - пример заполнения, attribute_decicion - поле, которое нужно заполнить подходящим значением опираясь на значения, которые содержаться в attribute_name, attribute_type, attribute_example. Задача: определи и заполни attribute_decicion подходящим значением конкретно для переданной номенклатурной позиции. Если не уверен, каким значением можно заполнить attribute_decicion, то оставь null.
        json схема: {json.dumps(attributes, ensure_ascii=False)}.
        Номенклатурная позиция: "{item_name}".
        Предоставляй в качестве вывода только сам json с заполненным attribute_decicion."""
        logger.info(f"-----> prompt:{prompt}")
        
        logger.info("----> Отправка запроса к ChatGPT")
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Ты полезный помощник, специализирующийся на классификации."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Ответ ChatGPT
        logger.info(f"----> Ответ получен от ChatGPT: {response}]")
        chatgpt_response = response['choices'][0]['message']['content']
        # Удаляем маркеры "```json" и "```"
        clean_string = chatgpt_response.replace('```json\n', '').replace('\n```', '')
        # Заменяем все экранированные кавычки на обычные кавычки
        clean_string = clean_string.replace(r'\\"', '"')
        # Преобразуем в JSON-объект
        logger.info(f"----> clean string: {clean_string}]")
        filled_attributes = json.loads(clean_string)

        logger.info(f"-----> att json result: {filled_attributes}")

        final_result = {"input_item_name": item_name,
                        "input_final_class_name": final_class_name,
                        "input_final_class_code": final_class_code,
                        "result": filled_attributes}

        logger.info(f"-----> final_result: {filled_attributes}")
        
        # Возвращаем заполненный JSON
        logger.info("----> Возвращение итогового JSON")
        return {
            'statusCode': 200,
            'body': json.dumps(final_result, ensure_ascii=False)
        }

    except Exception as e:
        logger.error(f"Ошибка выполнения: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Ошибка: {str(e)}", ensure_ascii=False)
        }
