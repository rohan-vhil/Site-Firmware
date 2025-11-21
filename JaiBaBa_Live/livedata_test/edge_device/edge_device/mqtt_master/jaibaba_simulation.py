import pika
import time
import json
import math
import random
import datetime

RABBITMQ_HOST = '3.110.77.154'
RABBITMQ_USER = 'enercog'
RABBITMQ_PASS = 'prod_enercog'
EXCHANGE_NAME = 'rpi'
EXCHANGE_TYPE = 'topic'
PUBLISH_QUEUE = 'live_data.jaibaba'
LISTEN_QUEUE = 'command.jaibaba'
PUBLISH_INTERVAL_SEC = 5

INVERTER_DATA = [
    {"device_id": "solar-inverter:SP-350K-INH:300007311248200206", "capacity_kw": 250},
    {"device_id": "solar-inverter:SPI250K-B-H:501501078430m9100014", "capacity_kw": 250},
    {"device_id": "solar-inverter:SG250HX:A2461105419", "capacity_kw": 320},
    {"device_id": "solar-inverter:SP-275K-INH:300009002234100111", "capacity_kw": 250},
    {"device_id": "solar-inverter:SPI250K-B-H:501501078430M9100010", "capacity_kw": 250},
    {"device_id": "solar-inverter:SPI250K-B-H:501501078430M9100004", "capacity_kw": 250},
    {"device_id": "solar-inverter:SG250HX:I2207200241", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000322", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000310", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000318", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000300", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000308", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:A2461105527", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000301", "capacity_kw": 320},
    {"device_id": "solar-inverter:SG320HX:I2452000312", "capacity_kw": 320}
]


def get_solar_factor(current_time):
    sunrise_hour = 6.0
    sunset_hour = 18.0
    hour = current_time.hour + current_time.minute / 60.0

    if not (sunrise_hour <= hour <= sunset_hour):
        return 0.0

    daylight_hours = sunset_hour - sunrise_hour
    normalized_time = (hour - sunrise_hour) / daylight_hours
    return math.sin(normalized_time * math.pi)


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection_params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials
    )

    while True:
        try:
            with pika.BlockingConnection(connection_params) as connection:
                channel = connection.channel()

                # Declare the exchange as topic
                channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE, durable=True)

                # Declare queues
                channel.queue_declare(queue=PUBLISH_QUEUE, durable=True)
                channel.queue_declare(queue=LISTEN_QUEUE, durable=True)

                # Bind queues to the topic exchange
                channel.queue_bind(exchange=EXCHANGE_NAME, queue=PUBLISH_QUEUE, routing_key=PUBLISH_QUEUE)
                channel.queue_bind(exchange=EXCHANGE_NAME, queue=LISTEN_QUEUE, routing_key=LISTEN_QUEUE)

                print(f"Connected. Publishing to '{PUBLISH_QUEUE}' via topic exchange '{EXCHANGE_NAME}'.")

                while True:
                    now = datetime.datetime.now()
                    now_utc_iso = now.astimezone(datetime.timezone.utc).isoformat()

                    solar_factor = get_solar_factor(now)
                    all_inverters_data = {}

                    for inverter in INVERTER_DATA:
                        capacity = inverter['capacity_kw']
                        base_power = capacity * solar_factor
                        noise = random.uniform(0.9, 1.1)
                        simulated_power = max(0.0, min(base_power * noise, capacity))
                        all_inverters_data[inverter['device_id']] = round(simulated_power, 2)

                    # Publish to topic exchange
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key=PUBLISH_QUEUE,
                        body=json.dumps(all_inverters_data),
                        properties=pika.BasicProperties(
                            content_type='application/json',
                            delivery_mode=2
                        )
                    )

                    print(f"[{now_utc_iso}] Published data for {len(all_inverters_data)} inverters. Factor: {solar_factor:.2f}")

                    # Listen for any commands
                    method_frame, header_frame, body = channel.basic_get(queue=LISTEN_QUEUE, auto_ack=True)
                    if method_frame:
                        print(f"Received command: {body.decode()}")

                    time.sleep(PUBLISH_INTERVAL_SEC)

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Simulation stopped by user.")
            break


if __name__ == "__main__":
    main()
