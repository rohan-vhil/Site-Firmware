import asyncio
import sys
from aio_pika import connect, Message, ExchangeType
from control import control_base as ctrl


async def main():
    rabbitmq_host = '16.171.145.138'
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

        severity = "project.test1.livedata"
        message_body = {"inverter:polycab:abc123":100, "grid":200, "dslgen":30, "battery":70, "load":400}

        message = Message(message_body.encode())
        await exchange.publish(message, routing_key=severity)

        print(f" [x] Sent {severity}:{message_body}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(" [*] Exiting...")
