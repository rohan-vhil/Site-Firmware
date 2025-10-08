import asyncio
import sys
from aio_pika import connect, Message, ExchangeType


async def main():
    rabbitmq_host = '13.60.65.220'
    username = 'variate'
    password = 'variate'

    connection = await connect(
        f"amqp://{username}:{password}@{rabbitmq_host}/"
    )

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            'direct_logs', ExchangeType.DIRECT
        )

        severity = sys.argv[1] if len(sys.argv) > 1 else 'info'
        message_body = ' '.join(sys.argv[2:]) or 'Hello World!'

        message = Message(message_body.encode())
        await exchange.publish(message, routing_key=severity)

        print(f" [x] Sent {severity}:{message_body}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(" [*] Exiting...")
