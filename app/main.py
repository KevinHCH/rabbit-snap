from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.requests import Request
from app.browser_manager import BrowserManager
from app.cache_manager import CacheManager
from app.rabbitmq_manager import RabbitMQManager
import asyncio
import uuid
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize managers
browser_manager = BrowserManager()
cache_manager = CacheManager("cache")
rabbitmq_manager = RabbitMQManager(host="localhost", queue_name="screenshot_queue")


MAX_CONCURRENT_SCREENSHOTS = 3
concurrency_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCREENSHOTS)


async def process_url(url: str, url_id: str):
    """Worker function to process URLs from RabbitMQ"""
    async with concurrency_semaphore:
        try:
            logger.info(f"Starting to process URL: {url} with ID: {url_id}")

            cached_image = cache_manager.get(url)
            if cached_image:
                logger.info(f"Cache hit for URL: {url}")
                await rabbitmq_manager.update_status(url_id, "done")
                return

            logger.info(f"Taking screenshot for URL: {url}")
            image_path = await browser_manager.capture_screenshot(url)
            cache_manager.set(url, image_path)
            rabbitmq_manager.update_status(url_id, "done")
            logger.info(f"Successfully processed URL: {url}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            rabbitmq_manager.update_status(url_id, "fail")
            raise


async def start_rabbitmq_consumer():
    """Start the RabbitMQ consumer asynchronously in the background."""
    logger.info("Starting RabbitMQ consumer...")
    try:
        # Keep consuming messages until stopped
        await rabbitmq_manager.start_consuming(process_url)
        logger.info("RabbitMQ consumer started successfully")
    except asyncio.CancelledError:
        logger.info("RabbitMQ consumer task cancelled")
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {str(e)}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the browser
    logger.info("Starting the browser...")
    await browser_manager.start()

    # Start RabbitMQ consumer in a background thread
    logger.info("Initializing RabbitMQ consumer...")
    consumer_task = asyncio.create_task(start_rabbitmq_consumer())

    logger.info("Application startup complete")

    yield

    logger.info("Starting cleanup...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled successfully")

    await browser_manager.stop()
    rabbitmq_manager.stop()
    logger.info("Cleanup complete")


app = FastAPI(lifespan=lifespan, debug=True)


@app.post("/screenshot")
async def take_screenshot(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        urls = data.get("urls", [])

        if not urls:
            raise HTTPException(status_code=400, detail="No URLs provided")

        # Process each URL
        processed_urls = []
        for url in urls:
            url_id = str(uuid.uuid4())
            logger.info(f"Publishing URL: {url} with ID: {url_id}")
            try:
                await rabbitmq_manager.publish(url, url_id)
                processed_urls.append({"url": url, "id": url_id})
            except Exception as e:
                logger.error(f"Error publishing URL {url}: {str(e)}")
                continue

        if not processed_urls:
            raise HTTPException(status_code=500, detail="Failed to queue any URLs")

        return JSONResponse(
            {
                "message": f"Queued {len(processed_urls)} URLs for processing",
                "urls": processed_urls,
            }
        )

    except Exception as e:
        logger.error(f"Error in take_screenshot endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    try:
        statuses = rabbitmq_manager.get_all_statuses()
        return JSONResponse(statuses)
    except Exception as e:
        logger.error(f"Error getting statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{url_id}")
async def get_status_url(url_id: str):
    try:
        status = rabbitmq_manager.get_status(url_id)
        if status is None:
            raise HTTPException(status_code=404, detail="URL not found")
        return JSONResponse({"url": url_id, "status": status})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for URL ID {url_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screenshot/lists")
async def list_screenshots():
    try:
        processed = [
            {"url": url, "image_path": cache_manager.get(url)}
            for url, status in rabbitmq_manager.status_tracker.items()
            if status == "done"
        ]
        return JSONResponse(processed)
    except Exception as e:
        logger.error(f"Error listing screenshots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
