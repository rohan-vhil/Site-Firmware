import asyncio
import json
import aio_pika
import datetime

RABBITMQ_URL = "amqp://enercog:enercog@16.171.145.138/"
EXCHANGE_NAME = "rpi"

async def main():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
    except Exception as e:
        print(f"Error connecting to RabbitMQ: {e}")
        return

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

        project_code_a = "solar_farm_001"
        project_code_b = "rooftop_solar_002"

        print("Publisher is running. Sending messages...")

        # live_data_payload = {
        #     "device_id": "inverter-A1",
        #     "power_kw": 150.5,
        #     "voltage": 480.2,
        #     "timestamp": datetime.datetime.now().isoformat()
        # }
        # live_data_message = aio_pika.Message(
        #     body=json.dumps(live_data_payload).encode(),
        #     delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        # )
        # routing_key_live = f"{project_code_a}.live_data"
        # await exchange.publish(live_data_message, routing_key=routing_key_live)
        # print(f" [x] Sent to '{routing_key_live}': {live_data_payload['power_kw']} kW")

        control_payload = {
            "mode": "time_of_use",
            "op_details": {
                "ref": 0,
                "batt_to_grid": True
            }
        }
        # control_payload = {
        #     "mode": "export_limit",
        #     "op_details": {
        #         "bat_to_load": True,
        #         "limit_export": True,
        #         "ref": 0
        #     }
        # }
        # control_payload = {
        #     "mode": "full",
        #     "op_details": {
        #         "ref": 0
        #     }
        # }
        control_message = aio_pika.Message(
            body=json.dumps(control_payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        routing_key_control = f"control.project1"
        await exchange.publish(control_message, routing_key=routing_key_control)
        print(f" [x] Sent to '{routing_key_control}': {control_payload}")
        
        print("\nMessages sent. Publisher is closing.")


if __name__ == "__main__":
    asyncio.run(main())