import asyncio
import sys
from aio_pika import connect, IncomingMessage, ExchangeType


async def main():
    rabbitmq_host = '16.171.145.138'
    username = 'vhileams'
    password = 'vhileams'

    connection = await connect(
        f"amqp://{username}:{password}@{rabbitmq_host}/"
    )
    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            'direct_logs', ExchangeType.DIRECT
        )

        queue = await channel.declare_queue(exclusive=True)

        severities = sys.argv[1:]
        if not severities:
            sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
            sys.exit(1)

        for severity in severities:
            await queue.bind(exchange, routing_key=severity)

        print(' [*] Waiting for logs. To exit press CTRL+C')

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(f" [x] {message.routing_key}: {message.body.decode()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(" [*] Exiting...")
