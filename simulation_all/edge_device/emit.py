import pika
import time
import json

RABBITMQ_HOST = '16.171.145.138'
RABBITMQ_USER = 'vhileams'
RABBITMQ_PASS = 'vhileams'
EXCHANGE_NAME = 'rpi'
ROUTING_KEY = 'control.project1'
MESSAGE = json.dumps({
    "mode" : "export_limit",
    "op_details" : {
        "ref" : 0
    }
})


def publish_message():
    try:
        print("try publishing")
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=MESSAGE,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f" [x] Sent '{MESSAGE}' with topic '{ROUTING_KEY}'")
        connection.close()

    except Exception as e:
        print(f"[!] Error publishing message: {e}")

if __name__ == '__main__':
    publish_message()
