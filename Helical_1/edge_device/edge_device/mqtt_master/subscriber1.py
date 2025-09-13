import pika
import sys

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}: {body.decode()}")

def main():
    rabbitmq_host = '13.60.65.220'
    username = 'variate'
    password = 'variate'

    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
    channel = connection.channel()

    channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue

    severities = sys.argv[1:]
    if not severities:
        sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
        sys.exit(1)

    for severity in severities:
        channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=severity)

    print(' [*] Waiting for logs. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [*] Exiting...")
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()