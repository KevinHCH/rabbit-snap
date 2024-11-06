import aio_pika
import json
import asyncio
from typing import Dict
import logging


logger = logging.getLogger(__name__)


class RabbitMQManager:
    def __init__(self, host: str = "localhost", queue_name: str = "screenshot_queue"):
        self.host = host
        self.queue_name = queue_name
        self.status_tracker: Dict[str, str] = {}
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish an async connection to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(host=self.host)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(self.queue_name, durable=True)
        logger.info("Successfully connected to RabbitMQ")

    async def publish(self, url: str, url_id: str):
        """Publish a URL to the RabbitMQ queue asynchronously"""
        await self.connect_if_needed()
        self.status_tracker[url_id] = "pending"
        message = {"url": url, "id": url_id}

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self.queue_name,
        )
        logger.info(f"Published message for URL: {url} with ID: {url_id}")

    async def connect_if_needed(self):
        """Ensure connection is active, reconnect if necessary"""
        if not self.connection or self.connection.is_closed:
            await self.connect()

    async def start_consuming(self, callback):
        """Start consuming messages from RabbitMQ queue asynchronously"""
        await self.connect_if_needed()
        queue = await self.channel.declare_queue(self.queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        url = data["url"]
                        url_id = data["id"]
                        logger.info(
                            f"Processing message for URL: {url} with ID: {url_id}"
                        )

                        # Run the callback
                        await callback(url, url_id)
                        self.update_status(url_id, "done")
                        logger.info(f"Successfully processed URL: {url}")
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {str(e)}")
                        self.update_status(url_id, "fail")

    def update_status(self, url_id: str, status: str):
        """Update the status of a URL in the status tracker"""
        if url_id in self.status_tracker:
            logger.info(f"Updating status for URL ID {url_id} to {status}")
            self.status_tracker[url_id] = status

    def get_status(self, url_id: str):
        """Get the status of a specific URL by ID"""
        return self.status_tracker.get(url_id)

    def get_all_statuses(self):
        """Get the status of all URLs"""
        return [
            {"url": url, "status": status}
            for url, status in self.status_tracker.items()
        ]

    async def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("RabbitMQ manager stopped")
