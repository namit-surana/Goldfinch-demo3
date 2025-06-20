# TIC Research API - Postman Testing Guide

## 🚀 Quick Start

1. **Start the API Server**:
   ```bash
   python start_api.py
   ```
   The server will be available at: `http://localhost:8000`

2. **Import the Collection** (see below for manual setup)

## 📋 API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Root endpoint |
| POST | `/research` | Start research |
| GET | `/research/{request_id}` | Get research results |
| GET | `/research/{request_id}/status` | Get research status |

## 🔧 Manual Postman Setup

### 1. Health Check
**Request:**
- Method: `GET`
- URL: `http://localhost:8000/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-20T17:02:14.402252",
  "version": "1.0.0"
}
```

### 2. Root Endpoint
**Request:**
- Method: `GET`
- URL: `http://localhost:8000/`

**Expected Response:**
```json
{
  "message": "TIC Research API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "start_research": "/research",
    "get_results": "/research/{request_id}",
    "get_status": "/research/{request_id}/status"
  }
}
```

### 3. Start Research
**Request:**
- Method: `POST`
- URL: `http://localhost:8000/research`
- Headers: `Content-Type: application/json`

**Body:**
```json
{
  "research_question": "What certifications are required to export electronics to the US?",
  "domain_list_metadata": [
    {
      "name": "UL (Underwriters Laboratories)",
      "homepage": "https://www.ul.com",
      "domain": "ul.com",
      "region": "United States",
      "org_type": "Private",
      "aliases": ["Underwriters Laboratories", "UL"],
      "industry_tags": ["Electronics", "Safety", "Certification"],
      "semantic_profile": "Leading global safety science company providing testing, inspection, and certification services for products and systems",
      "boost_keywords": ["safety", "certification", "testing", "standards", "compliance"]
    },
    {
      "name": "Consumer Product Safety Commission",
      "homepage": "https://www.cpsc.gov",
      "domain": "cpsc.gov",
      "region": "United States",
      "org_type": "Government",
      "aliases": ["CPSC", "Consumer Safety"],
      "industry_tags": ["Consumer Products", "Safety", "Regulation"],
      "semantic_profile": "Federal agency responsible for protecting the public from unreasonable risks of injury or death from consumer products",
      "boost_keywords": ["consumer safety", "product safety", "regulations", "standards", "compliance"]
    },
    {
      "name": "International Organization for Standardization",
      "homepage": "https://www.iso.org",
      "domain": "iso.org",
      "region": "International",
      "org_type": "StandardsBody",
      "aliases": ["ISO", "International Standards"],
      "industry_tags": ["Standards", "Certification", "Quality"],
      "semantic_profile": "International standard-setting body composed of representatives from various national standards organizations",
      "boost_keywords": ["standards", "certification", "quality", "compliance", "international"]
    }
  ],
  "chat_history": [
    {
      "role": "user",
      "content": "I need to export electronics to the US market"
    },
    {
      "role": "assistant",
      "content": "I can help you understand the certification requirements for exporting electronics to the US. Let me research the current standards and regulations."
    }
  ]
}
```

**Expected Response:**
```json
{
  "request_id": "4ba8c2f8-2211-4dde-9771-acfa2b51a24b",
  "status": "queued",
  "message": "Research request started successfully",
  "research_question": "What certifications are required to export electronics to the US?",
  "timestamp": "2025-06-20T17:02:14.402252"
}
```

### 4. Check Research Status
**Request:**
- Method: `GET`
- URL: `http://localhost:8000/research/{request_id}/status`
- Replace `{request_id}` with the ID from the previous response

**Expected Response:**
```json
{
  "request_id": "4ba8c2f8-2211-4dde-9771-acfa2b51a24b",
  "status": "processing",
  "message": "Router analyzing question...",
  "progress": 0.1
}
```

### 5. Get Research Results
**Request:**
- Method: `GET`
- URL: `http://localhost:8000/research/{request_id}`
- Replace `{request_id}` with the ID from the previous response

**Expected Response (Completed):**
```json
{
  "request_id": "4ba8c2f8-2211-4dde-9771-acfa2b51a24b",
  "status": "completed",
  "message": "Research completed successfully",
  "research_question": "What certifications are required to export electronics to the US?",
  "workflow_type": "provide_list_workflow",
  "execution_summary": {
    "total_time_seconds": 24.06,
    "workflow_type": "provide_list_workflow",
    "total_searches": 12,
    "general_searches": 6,
    "domain_searches": 6
  },
  "search_results": [
    {
      "query": "US certification requirements for importing electronics",
      "result": "Based on current research, the following certifications are typically required...",
      "citations": [...],
      "extracted_links": [...],
      "status": "success",
      "search_type": "general_web",
      "websites": []
    }
  ],
  "query_mappings": [
    {
      "query": "US certification requirements for importing electronics",
      "websites": [
        {
          "name": "UL (Underwriters Laboratories)",
          "domain": "ul.com"
        }
      ]
    }
  ],
  "timestamp": "2025-06-20T17:02:47.938746",
  "processing_time": 31.48
}
```

## 📝 Test Scenarios

### Scenario 1: Comprehensive Research (Provide_a_List)
**Question:** "What certifications are required to export electronics to the US?"

**Expected Workflow:** `provide_list_workflow`
**Expected Searches:** 12+ (6 general + 6 domain-filtered)

### Scenario 2: Specific Question (TIC_Specific_Questions)
**Question:** "How do I get UL certification for my product?"

**Expected Workflow:** `tic_specific_questions`
**Expected Searches:** 2 (1 general + 1 domain-filtered)

### Scenario 3: EU Standards
**Question:** "What safety standards apply to consumer products in the EU?"

**Expected Workflow:** `tic_specific_questions`
**Expected Searches:** 2 (1 general + 1 domain-filtered)

## 🔄 Testing Workflow

1. **Start Research** → Get `request_id`
2. **Check Status** → Monitor progress
3. **Get Results** → Retrieve final results

### Example Testing Sequence:

```bash
# 1. Health Check
GET http://localhost:8000/health

# 2. Start Research
POST http://localhost:8000/research
# Use the JSON body from above

# 3. Check Status (repeat until completed)
GET http://localhost:8000/research/{request_id}/status

# 4. Get Results
GET http://localhost:8000/research/{request_id}
```

## ⚠️ Error Handling

### Router Timeout
```json
{
  "status": "failed",
  "message": "Research failed - router timeout, no tool selected, or unknown tool"
}
```

### Invalid Request
```json
{
  "detail": [
    {
      "loc": ["body", "research_question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Request Not Found
```json
{
  "detail": "Research request not found"
}
```

## 🛠️ Postman Collection Setup

### 1. Create New Collection
- Name: `TIC Research API`
- Description: `Testing, Inspection, and Certification Research API`

### 2. Create Environment Variables
```
base_url: http://localhost:8000
request_id: (leave empty, will be set by tests)
```

### 3. Create Request Templates

#### Health Check Request
- Name: `Health Check`
- Method: `GET`
- URL: `{{base_url}}/health`

#### Start Research Request
- Name: `Start Research`
- Method: `POST`
- URL: `{{base_url}}/research`
- Headers: `Content-Type: application/json`
- Body: Use the JSON example above

#### Check Status Request
- Name: `Check Status`
- Method: `GET`
- URL: `{{base_url}}/research/{{request_id}}/status`

#### Get Results Request
- Name: `Get Results`
- Method: `GET`
- URL: `{{base_url}}/research/{{request_id}}`

### 4. Add Tests (Optional)

#### For Start Research:
```javascript
// Set request_id from response
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("request_id", response.request_id);
}
```

#### For Status Check:
```javascript
// Log status
if (pm.response.code === 200) {
    const response = pm.response.json();
    console.log(`Status: ${response.status} - ${response.message}`);
}
```

## 📊 Response Analysis

### Successful Research Response Structure:
- `request_id`: Unique identifier
- `status`: "completed", "failed", "processing"
- `workflow_type`: "provide_list_workflow" or "tic_specific_questions"
- `execution_summary`: Performance metrics
- `search_results`: Array of search results with content and citations
- `query_mappings`: How queries were mapped to websites
- `processing_time`: Total time taken

### Key Metrics to Monitor:
- **Processing Time**: Should be under 60 seconds
- **Total Searches**: Varies by workflow type
- **Success Rate**: All searches should have "success" status
- **Router Decision Time**: Should be under 15 seconds

## 🎯 Tips for Effective Testing

1. **Start with Health Check**: Ensure server is running
2. **Use Realistic Questions**: Test with actual TIC-related questions
3. **Monitor Status**: Check status endpoint during processing
4. **Verify Results**: Ensure search results contain relevant content
5. **Test Error Cases**: Try invalid requests and missing fields
6. **Check Performance**: Monitor processing times and search counts

## 🔍 Troubleshooting

### Common Issues:
1. **Server Not Running**: Check if `python start_api.py` is running
2. **Port Conflicts**: Ensure port 8000 is available
3. **API Key Issues**: Check environment variables in `.env`
4. **Timeout Errors**: Router timeout indicates LLM issues
5. **No Results**: Check if domain metadata is properly formatted

### Debug Steps:
1. Check server logs for errors
2. Verify API keys are set correctly
3. Test with simpler questions first
4. Check network connectivity
5. Verify JSON format in request body 