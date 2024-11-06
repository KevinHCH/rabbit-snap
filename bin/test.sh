# send multiple urls to process
curl -X POST "http://127.0.0.1:8000/screenshot" \
-H "Content-Type: application/json" \
-d '{"urls": ["https://marca.com", "https://github.com", "https://reddit.com"]}'
