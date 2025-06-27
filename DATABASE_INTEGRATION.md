# Database Integration Documentation

## Overview

This document describes the database integration for the TIC Research API, which provides persistent storage and analytics capabilities for LLM workflows.

## Architecture

### Database Layer
- **AWS RDS PostgreSQL**: Primary database for persistent storage
- **Async SQLAlchemy**: Async database operations
- **Connection Pooling**: Efficient connection management

### Service Layer
- **DatabaseService**: Core database operations
- **LLMDatabaseService**: LLM-specific database integration
- **Independent Endpoints**: REST API for database operations

## Setup Instructions

### 1. AWS RDS PostgreSQL Setup

1. **Create RDS Instance**:
   ```bash
   # Using AWS CLI
   aws rds create-db-instance \
     --db-instance-identifier tic-research-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username admin \
     --master-user-password your-secure-password \
     --allocated-storage 20 \
     --storage-type gp2
   ```

2. **Configure Security Groups**:
   - Allow inbound PostgreSQL (5432) from your application
   - Enable SSL connections

3. **Get Connection Details**:
   - Endpoint: `your-instance.region.rds.amazonaws.com`
   - Port: 5432
   - Database: `tic_research`

### 2. Environment Configuration

Copy `env_example.txt` to `.env` and configure:

```bash
# Database Configuration
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=tic_research
DB_USER=admin
DB_PASSWORD=your_secure_password

# Optional SSL Configuration
DB_SSL_MODE=require
```

### 3. Database Schema Setup

The database schema is defined in `database_schema.dbml`. To create the tables:

```sql
-- Create database
CREATE DATABASE tic_research;

-- Connect to database and run schema.sql
\c tic_research
\i database/schema.sql
```

## API Endpoints

### Database Health Check
```http
GET /db/health
```

**Response**:
```json
{
  "success": true,
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Session Management

#### Create Session
```http
POST /db/sessions/create
```

**Request**:
```json
{
  "user_id": "user123",
  "title": "Research Session",
  "metadata": {"source": "web"}
}
```

**Response**:
```json
{
  "success": true,
  "session": {
    "session_id": "session_20240101_120000_user123",
    "user_id": "user123",
    "title": "Research Session",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

#### Get Session
```http
GET /db/sessions/{session_id}
```

#### Update Session
```http
PUT /db/sessions/{session_id}
```

**Request**:
```json
{
  "title": "Updated Session Title",
  "is_active": true
}
```

#### Get User Sessions
```http
GET /db/sessions/user/{user_id}?limit=50&offset=0
```

### Message Management

#### Store Message
```http
POST /db/messages/store
```

**Request**:
```json
{
  "session_id": "session_123",
  "role": "user",
  "content": "What certifications do I need?",
  "metadata": {"tokens": 15}
}
```

**Response**:
```json
{
  "success": true,
  "message": {
    "message_id": "msg_20240101_120000_session123",
    "session_id": "session_123",
    "role": "user",
    "content": "What certifications do I need?",
    "message_order": 1,
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

#### Get Session Messages
```http
GET /db/messages/{session_id}?limit=50&offset=0&include_summarized=true
```

#### Get Recent Messages
```http
GET /db/messages/{session_id}/recent?count=10
```

### Research Management

#### Store Research Request
```http
POST /db/research/store
```

**Request**:
```json
{
  "session_id": "session_123",
  "research_question": "What certifications are needed for electronics?",
  "workflow_type": "Provide_a_List",
  "domain_metadata": {"domains": ["fda.gov", "ul.com"]}
}
```

**Response**:
```json
{
  "success": true,
  "request_id": "req_20240101_120000_session123",
  "message": "Research request stored successfully"
}
```

#### Update Research Request
```http
PUT /db/research/{request_id}
```

**Request**:
```json
{
  "status": "completed",
  "processing_time": 15.5,
  "query_strategy": {
    "workflow_type": "Provide_a_List",
    "total_searches": 3
  }
}
```

#### Get Research Request
```http
GET /db/research/{request_id}
```

#### Get Research History
```http
GET /db/research/history/{session_id}?limit=10
```

### Analytics

#### Log Analytics Event
```http
POST /db/analytics/log
```

**Request**:
```json
{
  "event_type": "research_completed",
  "event_data": {
    "request_id": "req_123",
    "processing_time": 15.5
  },
  "session_id": "session_123",
  "performance_data": {
    "response_time": 1.2,
    "tokens_used": 150
  }
}
```

#### Get Analytics Summary
```http
GET /db/analytics/summary?days=30
```

### Context Retrieval

#### Get Research Context
```http
GET /db/context/{session_id}?message_count=10
```

**Response**:
```json
{
  "success": true,
  "context": {
    "session": {...},
    "recent_messages": [...],
    "research_history": [...],
    "enhanced_history": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
}
```

## LLM Integration

### Using LLMDatabaseService

```python
from database.services.llm_db_service import get_llm_db_service

# Get service instance
llm_db = get_llm_db_service()

# Get research context
context = await llm_db.get_research_context(session_id, chat_history)

# Start research workflow
request_id = await llm_db.start_research_workflow(
    session_id=session_id,
    research_question="What certifications are needed?",
    workflow_type="Provide_a_List"
)

# Store messages
await llm_db.store_user_message(session_id, "User question")
await llm_db.store_assistant_message(session_id, "Assistant response")

# Complete workflow
await llm_db.complete_research_workflow(request_id, result_data)

# Log performance
await llm_db.log_llm_performance(
    event_type="router_decision",
    performance_data={"response_time": 1.5}
)
```

### Enhanced Workflow Integration

Update your existing workflows to use database integration:

```python
# In workflows.py
async def route_research_request(self, research_question: str, chat_history: Optional[List[Dict]] = None):
    # Get LLM database service
    llm_db = get_llm_db_service()
    
    # Get enhanced context from database
    context = await llm_db.get_research_context(session_id, chat_history)
    enhanced_history = context["enhanced_history"]
    
    # Start research workflow tracking
    request_id = await llm_db.start_research_workflow(
        session_id=session_id,
        research_question=research_question,
        workflow_type="pending"
    )
    
    try:
        # Get router decision with enhanced context
        router_answer = await self.openai_service.get_router_decision(
            research_question, enhanced_history
        )
        
        # Update workflow type
        await llm_db.db_service.update_research_request(
            request_id, {"workflow_type": router_answer["type"]}
        )
        
        # Execute workflow
        result = await self.execute_workflow(router_answer["type"], research_question, queries)
        
        # Complete workflow
        await llm_db.complete_research_workflow(request_id, result)
        
        return result
        
    except Exception as e:
        # Log error
        await llm_db.log_research_error(request_id, str(e), session_id)
        raise
```

## Testing

### Run Integration Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env_example.txt .env
# Edit .env with your database credentials

# Run tests
python test_database_integration.py
```

### Manual Testing

```bash
# Start the API server
python start_api.py

# Test endpoints
curl http://localhost:8000/db/health
curl -X POST http://localhost:8000/db/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "title": "Test Session"}'
```

## Performance Considerations

### Connection Pooling
- Default pool size: 10 connections
- Max overflow: 20 connections
- Pool recycle: 1 hour
- Pool pre-ping: Enabled

### Query Optimization
- Use indexes on frequently queried columns
- Implement pagination for large result sets
- Use async operations for better concurrency

### Caching Strategy
- Implement Redis for frequently accessed data
- Cache research results for similar queries
- Use database connection pooling

## Monitoring

### Database Metrics
- Connection pool utilization
- Query performance
- Error rates
- Storage usage

### Application Metrics
- Request/response times
- Success/failure rates
- User activity patterns
- Research workflow performance

### Logging
- Database operations are logged with appropriate levels
- Analytics events provide insights into usage patterns
- Error logging includes context for debugging

## Security

### Database Security
- SSL/TLS encryption for connections
- VPC isolation for RDS instance
- IAM roles for access control
- Regular security updates

### API Security
- Input validation on all endpoints
- Rate limiting for abuse prevention
- Authentication (to be implemented)
- Audit logging for compliance

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check database credentials
   - Verify network connectivity
   - Ensure security group allows connections

2. **Performance Issues**:
   - Monitor connection pool usage
   - Check query performance
   - Review indexing strategy

3. **Data Consistency**:
   - Use transactions for related operations
   - Implement proper error handling
   - Monitor for data integrity issues

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export DB_ECHO=true  # SQL query logging
```

## Future Enhancements

1. **Caching Layer**: Redis integration for performance
2. **Real-time Analytics**: WebSocket connections for live metrics
3. **Advanced Search**: Full-text search capabilities
4. **Data Export**: CSV/JSON export functionality
5. **Backup/Restore**: Automated backup strategies
6. **Multi-tenancy**: Support for multiple organizations 