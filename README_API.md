# TIC Research API

A FastAPI-based REST API for Testing, Inspection, and Certification (TIC) industry research with dynamic domain configuration.

## 🚀 Features

- **Dynamic Domain Configuration**: Accept custom domain metadata for flexible TIC website targeting
- **Chat History Context**: Include previous conversation context for better research
- **Async Processing**: Background task processing with status tracking
- **Intelligent Routing**: Smart workflow selection based on question type
- **Comprehensive Results**: Detailed research results with execution summaries
- **Timeout Handling**: Robust error handling with 15-second router timeout

## 📋 Requirements

### Core Dependencies
```bash
pip install -r requirements.txt
```

### API Dependencies
```bash
pip install -r requirements_api.txt
```

## 🏃‍♂️ Quick Start

### 1. Start the API Server
```bash
python api_server.py
```

The server will start on `http://localhost:8000`

### 2. Test the API
```bash
python test_api_client.py
```

## 📚 API Endpoints

### POST `/research`
Start a new research request.

**Request Body:**
```json
{
  "research_question": "What certifications are required to export electronics to the US?",
  "domain_list_metadata": [
    {
      "name": "Consumer Product Safety Commission (CPSC)",
      "homepage": "https://www.cpsc.gov",
      "domain": "cpsc.gov",
      "region": "United States",
      "org_type": "Government",
      "aliases": ["CPSC"],
      "industry_tags": ["SafetyRegulator", "ConsumerGoods"],
      "semantic_profile": "The Consumer Product Safety Commission...",
      "boost_keywords": ["consumer safety regulations", "product recall CPSC", ...]
    }
  ],
  "chat_history": [
    {
      "role": "user",
      "content": "What certifications are necessary to import condom to China"
    }
  ],
  "target_domains": ["cpsc.gov", "ul.com"]
}
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Research request started successfully",
  "research_question": "What certifications are required to export electronics to the US?",
  "timestamp": "2024-01-15T10:30:00"
}
```

### GET `/research/{request_id}`
Get research results by request ID.

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Research completed successfully",
  "research_question": "What certifications are required to export electronics to the US?",
  "workflow_type": "provide_list_workflow",
  "execution_summary": {
    "total_time_seconds": 45.2,
    "total_searches": 8,
    "general_searches": 4,
    "domain_searches": 4
  },
  "search_results": [...],
  "query_mappings": [...],
  "timestamp": "2024-01-15T10:30:45",
  "processing_time": 45.2
}
```

### GET `/research/{request_id}/status`
Get research status by request ID.

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Router analyzing question...",
  "progress": 0.1
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

## 🔧 Domain Metadata Structure

Each domain in `domain_list_metadata` should have the following structure:

```json
{
  "name": "Organization Name",
  "homepage": "https://www.example.com",
  "domain": "example.com",
  "region": "United States",
  "org_type": "Government|Private|StandardsBody",
  "aliases": ["Alias1", "Alias2"],
  "industry_tags": ["Electronics", "ConsumerGoods"],
  "semantic_profile": "Detailed description of the organization's role and expertise...",
  "boost_keywords": ["keyword1", "keyword2", "keyword3"]
}
```

## 📊 Response Statuses

- **`queued`**: Request accepted and queued for processing
- **`processing`**: Research is currently being processed
- **`completed`**: Research completed successfully
- **`failed`**: Research failed (router timeout, no tool selected, etc.)
- **`error`**: System error occurred during processing

## 🛠️ Usage Examples

### Python Client Example
```python
import requests

# Start research
payload = {
    "research_question": "What certifications are required to export electronics to the US?",
    "domain_list_metadata": [...],  # Your domain metadata
    "chat_history": [...],          # Your chat history
    "target_domains": ["cpsc.gov", "ul.com"]
}

response = requests.post("http://localhost:8000/research", json=payload)
request_id = response.json()["request_id"]

# Check status
status_response = requests.get(f"http://localhost:8000/research/{request_id}/status")
print(status_response.json())

# Get results
results_response = requests.get(f"http://localhost:8000/research/{request_id}")
print(results_response.json())
```

### cURL Example
```bash
# Start research
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "research_question": "What certifications are required to export electronics to the US?",
    "domain_list_metadata": [...],
    "chat_history": [...],
    "target_domains": ["cpsc.gov", "ul.com"]
  }'

# Check status
curl "http://localhost:8000/research/{request_id}/status"

# Get results
curl "http://localhost:8000/research/{request_id}"
```

## 🔍 Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input (empty research question, missing domain metadata)
- **404 Not Found**: Request ID not found
- **500 Internal Server Error**: System errors

### Router Timeout
If the router takes more than 15 seconds to decide which tool to use:
```json
{
  "status": "failed",
  "message": "Research failed - router timeout, no tool selected, or unknown tool"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Client    │───▶│  FastAPI Server  │───▶│ TIC Research    │
│                 │    │                  │    │ Workflow        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Background Tasks │
                       │ (Async Processing)│
                       └──────────────────┘
```

## 🔧 Configuration

The API uses the same configuration as the main TIC research system:

- **OpenAI API**: Configured in `config.py`
- **Perplexity API**: Configured in `api_services.py`
- **Environment Variables**: Loaded from `.env` file

## 📝 Notes

- The API processes requests asynchronously using FastAPI's background tasks
- Results are stored in memory (not persistent across server restarts)
- Each request gets a unique UUID for tracking
- The system uses dynamic domain configuration instead of hardcoded TIC websites
- Chat history provides context for better research results

## 🚀 Deployment

For production deployment, consider:

1. **Database Storage**: Store results in a database instead of memory
2. **Redis Queue**: Use Redis for background task processing
3. **Load Balancing**: Deploy multiple instances behind a load balancer
4. **Authentication**: Add API key authentication
5. **Rate Limiting**: Implement rate limiting for API endpoints

## 📄 License

This API is part of the TIC Research System and follows the same license terms. 