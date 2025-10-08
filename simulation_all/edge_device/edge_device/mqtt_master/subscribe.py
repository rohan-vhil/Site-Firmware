import pika
import time
from control import control_base as ctrl

RABBITMQ_HOST = '16.171.145.138'
RABBITMQ_USER = 'vhileams'
RABBITMQ_PASS = 'vhileams'
EXCHANGE_NAME = 'rpi'
ROUTING_KEY = 'control.project1'

def start_subscriber():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
            channel = connection.channel()

            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
            result = channel.queue_declare(queue='', durable=True, exclusive=True)
            queue_name = result.method.queue

            channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=ROUTING_KEY)

            print(' [*] Waiting for messages. To exit press CTRL+C')

            def callback(ch, method, properties, body):
                try:
                    print(f" [x] Received {body.decode()}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    #callFunc()
                    ctrl.processMQTTMessage(body.decode())
                except Exception as e:
                    print(f"[!] Error in message callback: {e}")

            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            channel.start_consuming()

        except Exception as e:
            print(f"[!] Subscriber error: {e}")
            time.sleep(5) 

if __name__ == '__main__':
    start_subscriber()
