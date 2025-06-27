# Database Module

This module contains all database-related functionality for the TIC Research API, organized in a clean, modular structure.

## 📁 Folder Structure

```
database/
├── README.md                 # This file
├── __init__.py              # Database module initialization
├── models.py                # SQLAlchemy ORM models
├── schema.sql               # Database schema definitions
├── connection.py            # Database connection utilities
├── services/                # Database service layer
│   ├── __init__.py         # Services package initialization
│   ├── database_service.py # Core database operations
│   └── llm_db_service.py   # LLM-database integration
└── api/                     # Database API endpoints
    ├── __init__.py         # API package initialization
    └── database_endpoints.py # REST API endpoints
```

## 🏗️ Architecture Overview

### **Services Layer (`services/`)**
The services layer provides the core database functionality:

#### **DatabaseService** (`services/database_service.py`)
- **Session Management**: Create, read, update sessions
- **Message Storage**: Store and retrieve chat messages
- **Research Tracking**: Complete research request lifecycle
- **Analytics Logging**: Event tracking and performance monitoring
- **Connection Management**: Async SQLAlchemy with connection pooling

#### **LLMDatabaseService** (`services/llm_db_service.py`)
- **Context Management**: Enhanced research context retrieval
- **Workflow Integration**: Seamless LLM workflow integration
- **Performance Monitoring**: LLM-specific performance tracking
- **Memory Management**: Conversation memory and caching
- **Analytics**: Session-level analytics and insights

### **API Layer (`api/`)**
The API layer provides REST endpoints for database operations:

#### **Database Endpoints** (`api/database_endpoints.py`)
- **Session Endpoints**: `/db/sessions/*` for session management
- **Message Endpoints**: `/db/messages/*` for chat operations
- **Research Endpoints**: `/db/research/*` for research tracking
- **Analytics Endpoints**: `/db/analytics/*` for event logging
- **Context Endpoints**: `/db/context/*` for LLM context retrieval

## 🚀 Quick Start

### **1. Import Services**
```python
# Import database services
from database.services import get_database_service, get_llm_db_service

# Get service instances
db_service = get_database_service()
llm_db_service = get_llm_db_service()
```

### **2. Use Database Service**
```python
# Create session
session = await db_service.create_session(user_id, title)

# Store message
message = await db_service.store_message(session_id, role, content)

# Store research request
request_id = await db_service.store_research_request(
    session_id, question, workflow_type
)
```

### **3. Use LLM Integration**
```python
# Get research context
context = await llm_db_service.get_research_context(session_id, chat_history)

# Start research workflow
request_id = await llm_db_service.start_research_workflow(
    session_id, question, workflow_type
)

# Store messages
await llm_db_service.store_user_message(session_id, content)
await llm_db_service.store_assistant_message(session_id, content)
```

### **4. Use API Endpoints**
```python
# Health check
GET /db/health

# Create session
POST /db/sessions/create
{
    "user_id": "user123",
    "title": "Research Session"
}

# Store message
POST /db/messages/store
{
    "session_id": "session_123",
    "role": "user",
    "content": "What certifications do I need?"
}

# Get context
GET /db/context/{session_id}
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Database Configuration
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=tic_research
DB_USER=your_db_username
DB_PASSWORD=your_db_password

# Optional SSL Configuration
DB_SSL_MODE=require
```

### **Database Schema**
The database schema is defined in `schema.sql` and includes:
- **Users & Sessions**: Multi-user support with conversation management
- **Chat Messages**: Message storage with ordering and metadata
- **Research Requests**: Complete audit trail of research operations
- **Analytics**: Event tracking and performance monitoring
- **Domain Sets**: Configurable domain metadata
- **Result Cache**: Caching for improved performance

## 📊 Features

### **Core Database Operations**
- ✅ **Async Operations**: Full async support with SQLAlchemy
- ✅ **Connection Pooling**: Efficient connection management
- ✅ **Transaction Support**: ACID compliance with rollback support
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Performance Monitoring**: Query performance tracking

### **LLM Integration**
- ✅ **Context Retrieval**: Enhanced research context with history
- ✅ **Workflow Tracking**: Complete research workflow lifecycle
- ✅ **Message Storage**: User and assistant message persistence
- ✅ **Performance Logging**: LLM-specific performance metrics
- ✅ **Analytics**: Session-level insights and analytics

### **API Endpoints**
- ✅ **RESTful Design**: Clean, consistent API design
- ✅ **Input Validation**: Comprehensive request validation
- ✅ **Error Responses**: Detailed error messages and status codes
- ✅ **Documentation**: Auto-generated API documentation
- ✅ **Health Checks**: Database health monitoring

## 🧪 Testing

### **Run Integration Tests**
```bash
# Run database integration tests
python test_database_integration.py
```

### **Test Coverage**
- ✅ **Database Service**: Direct service testing
- ✅ **API Endpoints**: HTTP endpoint testing
- ✅ **LLM Integration**: LLM-database integration testing
- ✅ **Error Handling**: Error scenario testing
- ✅ **Performance**: Performance and load testing

## 📈 Performance

### **Connection Pooling**
- **Pool Size**: 10 connections (configurable)
- **Max Overflow**: 20 connections
- **Pool Recycle**: 1 hour
- **Pool Pre-ping**: Enabled for connection health

### **Query Optimization**
- **Indexed Queries**: Optimized for common query patterns
- **Async Operations**: Non-blocking database operations
- **Batch Operations**: Efficient bulk operations
- **Caching**: Result caching for improved performance

### **Monitoring**
- **Query Performance**: Slow query detection and optimization
- **Connection Health**: Connection pool monitoring
- **Error Rates**: Database error tracking
- **Usage Analytics**: Database usage patterns

## 🔒 Security

### **Database Security**
- **SSL/TLS**: Encrypted database connections
- **VPC Isolation**: Network-level security
- **IAM Roles**: AWS IAM integration
- **Access Control**: User-level permissions

### **API Security**
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Abuse prevention
- **Authentication**: User authentication (to be implemented)
- **Audit Logging**: Complete audit trail

## 🚀 Deployment

### **AWS RDS Setup**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier tic-research-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password your-secure-password \
  --allocated-storage 20 \
  --storage-type gp2
```

### **Schema Migration**
```sql
-- Create database
CREATE DATABASE tic_research;

-- Run schema
\c tic_research
\i database/schema.sql
```

### **Environment Setup**
```bash
# Copy environment template
cp env_example.txt .env

# Configure database settings
DB_HOST=your-rds-endpoint
DB_USER=admin
DB_PASSWORD=your-secure-password
```

## 🔄 Integration

### **With Main Application**
The database module integrates seamlessly with the main TIC Research API:

```python
# In main application
from database.services import get_llm_db_service

# Use in workflows
llm_db = get_llm_db_service()
context = await llm_db.get_research_context(session_id, chat_history)
```

### **With FastAPI**
```python
# In FastAPI app
from database.api import database_endpoints

# Include database routes
app.include_router(database_endpoints.db_router)
```

## 📚 Documentation

### **API Documentation**
- **Swagger UI**: Available at `/docs` when running the API
- **OpenAPI Spec**: Auto-generated API specification
- **Code Examples**: Comprehensive usage examples
- **Error Codes**: Detailed error documentation

### **Database Schema**
- **DBML**: Visual database schema representation
- **SQL Scripts**: Complete schema creation scripts
- **Migration Guide**: Database migration procedures
- **Indexing Strategy**: Performance optimization guide

## 🤝 Contributing

### **Code Organization**
- **Services**: Business logic in service classes
- **API**: REST endpoints in API modules
- **Models**: Data models in models.py
- **Schema**: Database schema in schema.sql

### **Testing Guidelines**
- **Unit Tests**: Test individual service methods
- **Integration Tests**: Test database integration
- **API Tests**: Test REST endpoints
- **Performance Tests**: Test database performance

### **Code Standards**
- **Type Hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Proper exception handling
- **Logging**: Structured logging throughout

## 🔮 Future Enhancements

### **Planned Features**
1. **Redis Caching**: Performance optimization with Redis
2. **Real-time Analytics**: WebSocket-based live metrics
3. **Advanced Search**: Full-text search capabilities
4. **Data Export**: CSV/JSON export functionality
5. **Backup/Restore**: Automated backup strategies
6. **Multi-tenancy**: Support for multiple organizations

### **Performance Improvements**
1. **Query Optimization**: Advanced query optimization
2. **Connection Pooling**: Enhanced connection management
3. **Caching Strategy**: Multi-level caching
4. **Indexing**: Advanced indexing strategies
5. **Partitioning**: Database partitioning for large datasets

This modular database structure provides a solid foundation for scaling the TIC Research API while maintaining clean separation of concerns and excellent maintainability. 