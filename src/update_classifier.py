import json
import os
import redis
from redis.commands.json.path import Path
import logging

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Чтение переменных окружения для подключения
        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        
        # Настройка подключения к Redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        
        # Проверка соединения с Redis
        try:
            r.ping()
        except redis.ConnectionError:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Could not connect to Redis'})
            }
        logger.info("----------> Successfully connected to Redis.")
        
        # Извлечение тела запроса
        body = json.loads(event['body'])
        
        logger.info("----------> Received request body: %s", body)
    
        # Подготовка данных для пакетной загрузки
        pipeline = r.pipeline()
        
        # Обновление классификатора в Redis
        for entry in body:
            key = entry['key']
            data = entry['data']
            pipeline.json().set(key, Path.root_path(), data)  # Используем pipeline для пакетной загрузки
        
        logger.info("----------> Подготовлены данные для пакетной загрузки с использованием JSON.MSET: %s", pipeline)
        pipeline.execute()  # Выполнение всех команд в пайплайне
        logger.info("----------> Данные успешно загружены в Redis")
        
        # Формируем ответ
        response = {
            "result": "OK"
        }
        
        # Возвращаем результат с успешным кодом 200
        return {
            'statusCode': 200,
            'body': json.dumps(response, ensure_ascii=False),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
