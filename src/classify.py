import json
import os
import openai
import redis
from redis.commands.json.path import Path

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Извлекаем параметр "itemName" из строки запроса
        logger.info("--------> EVENT", event)
        item_description = event['queryStringParameters'].get('itemName')
        logger.info("--------> ITEM NAME", item_description)
        
        # Проверка, передан ли параметр
        if not item_description:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing "itemName" parameter'})
            }
            
        # Чтение переменных окружения для подключения
        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        OPENAI_TOKEN = os.getenv('OPENAI_TOKEN', 'empty')
        MODEL = "gpt-4o"
        TEMPERATURE = 0

        openai.api_key = OPENAI_TOKEN
        
        # Настройка подключения к Redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        # Проверка соединения с Redis
        r.ping()
        
        logger.info("\n--------> Processing item:", item_description)
    
        # Используем SCAN вместо KEYS для производительности
        result_classify = []
        
        for i in range(7):
            # Для первой итерации выбираем все ключи первого уровня
            if i == 0:
                current_сlass_code = "0000000000000"
            
            keys = r.keys(f"{current_сlass_code}*")
            logger.info(f"\n--------> Keys at level {i+1}: {keys}")
            
            if not keys:
                logger.info(f"\n--------> Final class found: {found_class}, stopping")
                break
            
            # Получаем JSON объекты из Redis
            classes = r.json().mget(keys, Path.root_path())
            classes = [c for c in classes if c]  # Фильтруем пустые объекты
            
            if not classes:
                logger.info(f"\n--------> No data found for class at depth {depth}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': f'Класс с наименованием "{result_class}" и кодом "{found_class_code}" пустой (не содержит данных).',
                        'input_item_name': item_description,
                        'class_name': result_class,
                        'class_code': found_class_code
                    }, ensure_ascii=False),
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
                break
            
            classes_names = [item.get("name") for item in classes if "name" in item]
            logger.info(f"\n--------> Class names: {classes_names}")
            
            # Подготавливаем prompt для OpenAI
            actual_names_str = "; ".join(f'"{x}"' for x in classes_names)
            prompt =f'''Задача: определить наиболее подходящую категорию для номенклатурной позиции из предложенного списка категорий. Категории: {actual_names_str}.
            Номенклатурная позиция: "{item_description}".
            Выбери одну наиболее подходящую категорию из предложенного списка для данной номенклатурной позиции.
            Предоставляй в качестве вывода только наиболее подходящее имя категории. Вывод не должен содержать кавычки и другие спецсимволы.'''

            messages = [{"role": "system", "content": "Ты полезный помощник, специализирующийся на классификации."},
                        {"role": "user", "content": prompt}]
            
            # Вызов модели OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model=MODEL,
                    messages=messages,
                    temperature=TEMPERATURE
                )
            except openai.error.OpenAIError as e:
                logger.info(f"OpenAI API error: {e}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": "OpenAI API error", "details": str(e)})
                }
            
            result_class = response['choices'][0]['message']['content'].strip()
            logger.info(f"Resulting class at level {i+1}: {result_class}")
            
            # Поиск кода класса
            found_class = next((item for item in classes if item.get("name") == result_class), None)
            if not found_class:
                logger.info(f"Class '{result_class}' not found in Redis")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': f"Class '{result_class}' not found in Redis"
                    }, ensure_ascii=False),
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
                break
            
            found_class_code = found_class['code']
            result_classify.append({
                "class_name": result_class,
                "class_code": found_class_code
            })
            
            # Увеличиваем значение фильтра по коду класса для следующей итерации
            current_сlass_code = found_class_code[2:]
        
        # Формируем результат
        result = {
            "input_item_name": item_description,
            "result": result_classify
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, ensure_ascii=False),
            'headers': {'Content-Type': 'application/json'}
        }
    
    except redis.ConnectionError as e:
        logger.info(f"Redis connection error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Redis connection error", "details": str(e)})
        }
    except Exception as e:
        logger.info(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }
