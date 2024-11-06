# RABBIT-SNAP

This project was born from repeated client requests for a page, service, or API that could capture screenshots of other websites. Here, I decided to build it with **Python** and **FastAPI**, using headless browsers powered by **Playwright** for both ease of development and deployment.

The service exposes several endpoints (check the FastAPI-generated documentation for details). Among them, the endpoint `POST /screenshots` is especially useful: it allows you to send a JSON payload with an array of URLs, which are then added to a **RabbitMQ queue** and processed asynchronously in sequence. The architecture of this project makes it suitable for running on low-power machines or even as **AWS Lambda functions**.

After the images have been processed, you can retrieve the screenshots from the endpoint `GET /screenshot/list`. This setup ensures that the Python threads remain unblocked, maintaining an asynchronous flow across the system.

## Key Features

- **Asynchronous Processing**: Screenshots are processed asynchronously, making this service responsive and scalable.
- **Queue-Based Workflow**: URLs sent to the `/screenshots` endpoint are queued in RabbitMQ, ensuring orderly and reliable processing.
- **Headless Browser Support**: Uses Playwright for capturing high-quality screenshots from headless browsers.
- **Containerized for Portability**: Dockerized for easy deployment on any environment that supports Docker.

## Technology Stack

- **Python**: Core language for building the API and business logic.
- **FastAPI**: Modern, fast (high-performance), web framework for building APIs with Python.
- **Playwright**: Headless browser support for accurate and customizable screenshot capture.
- **RabbitMQ**: Queue service to handle requests in a non-blocking, asynchronous manner.
- **Docker**: Containerizes the app, making it highly portable across environments.

## Endpoints Overview

### `/screenshots`
- **Method**: POST
- **Description**: Accepts a JSON array of URLs. Each URL is added to the RabbitMQ queue and processed in sequence.
- **Request Example**:
    ```json
    {
      "urls": ["https://example.com", "https://anotherpage.com"]
    }
    ```

### `/screenshot/list`
- **Method**: GET
- **Description**: Retrieves a list of all processed screenshots along with their URLs.
  
### **Other Endpoints**
For a full list of endpoints and their descriptions, please refer to the FastAPI-generated documentation at `/docs`.

## Setup & Installation

### Prerequisites
- **Docker** (for containerized setup)
- **Python 3.12** (if running locally without Docker)
- **RabbitMQ** (can also be set up as a separate container)

### Run with Docker

1. **Clone the repository**:
    ```bash
    git clone https://github.com/kevinHCH/rabbit-snap.git
    cd rabbit-snap
    ```

2. **Build the Docker image**:
    ```bash
    docker build -t rabbit-snap .
    ```

3. **Run the container**:
    ```bash
    docker run -p 8000:8000 rabbit-snap
    ```

### Local Setup

1. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2. **Run the application**:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

## How It Works

1. **Submitting URLs**: You can submit an array of URLs to the `/screenshots` endpoint. Each URL is added to a RabbitMQ queue for sequential processing.
2. **Async Processing**: Using asynchronous processing, the system captures screenshots of each URL in the queue without blocking the main application thread.
3. **Retrieving Screenshots**: Processed screenshots are accessible via the `/screenshot/list` endpoint, keeping the flow responsive and non-blocking.

## Ideal Use Cases

- **Serverless Environments**: Works well on platforms like AWS Lambda due to its asynchronous and non-blocking design.
- **Resource-Constrained Machines**: Efficient queue-based processing allows it to run on machines with limited resources.
  
## License

This project is open-source and licensed under the MIT License.
