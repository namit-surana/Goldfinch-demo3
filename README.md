# TIC Research API

A comprehensive Testing, Inspection, and Certification (TIC) research API built with FastAPI, OpenAI, and Perplexity AI. This system provides intelligent research capabilities for compliance and certification requirements across global markets.

## 🏗️ Modular Project Structure

```
tic-research-api/
├── 📁 src/                          # Core application code
│   ├── 📁 core/                     # Core business logic
│   │   ├── __init__.py
│   │   └── workflows.py             # Research workflows and business logic
│   ├── 📁 models/                   # Data models and schemas
│   │   ├── __init__.py
│   │   ├── requests.py              # Request models (ResearchRequest, ChatMessage)
│   │   ├── responses.py             # Response models (ResearchResultResponse, etc.)
│   │   └── domain.py                # Domain metadata models
│   ├── 📁 services/                 # External service integrations
│   │   ├── __init__.py
│   │   ├── openai_service.py        # OpenAI API integration
│   │   └── perplexity_service.py    # Perplexity AI integration
│   ├── 📁 api/                      # API layer
│   │   ├── __init__.py
│   │   ├── server.py                # FastAPI server configuration
│   │   └── endpoints.py             # API endpoints
│   ├── 📁 config/                   # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py              # App settings and constants
│   │   └── prompts.py               # AI prompts and system messages
│   └── 📁 utils/                    # Utilities
│       ├── __init__.py
│       └── helpers.py               # Helper functions
├── 📁 database/                     # Database module (NEW STRUCTURE)
│   ├── 📁 services/                 # Database service layer
│   │   ├── __init__.py
│   │   ├── database_service.py      # Core database operations
│   │   └── llm_db_service.py        # LLM-database integration
│   ├── 📁 api/                      # Database API endpoints
│   │   ├── __init__.py
│   │   └── database_endpoints.py    # REST API for database operations
│   ├── __init__.py                  # Database module initialization
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schema.sql                   # Database schema definitions
│   ├── connection.py                # Database connection utilities
│   └── README.md                    # Database module documentation
├── 📁 tests/                        # Test files
│   ├── test_api_client.py           # API client tests
│   └── test_structured_output.py    # Structured output tests
├── 🐍 start_api.py                  # Application entry point
├── 📄 requirements.txt              # Python dependencies
├── 📄 render.yaml                   # Render deployment configuration
├── 📄 env_example.txt               # Environment variables template
├── 📄 test_database_integration.py  # Database integration tests
├── 📄 DATABASE_INTEGRATION.md       # Database integration documentation
└── 📄 README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Perplexity AI API key
- AWS RDS PostgreSQL (for database functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tic-research-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys and database configuration
   ```

4. **Set up database (optional)**
   ```bash
   # Configure AWS RDS PostgreSQL
   # Update .env with database credentials
   # Run database integration tests
   python test_database_integration.py
   ```

5. **Start the API server**
   ```bash
   python start_api.py
   ```

The API will be available at `http://localhost:8000`

## 🏛️ Architecture Overview

### **Modular Design Principles**

The project follows a clean, modular architecture with clear separation of concerns:

#### **1. Core Module (`src/core/`)**
- **Purpose**: Contains the main business logic
- **Key Components**:
  - `TICResearchWorkflow`: Base workflow class
  - `DynamicTICResearchWorkflow`: Extended workflow with dynamic domain metadata
- **Responsibilities**: Research routing, workflow execution, result processing

#### **2. Models Module (`src/models/`)**
- **Purpose**: Data models and schemas using Pydantic
- **Key Components**:
  - `requests.py`: API request models
  - `responses.py`: API response models and structured output schemas
  - `domain.py`: Domain metadata models
- **Benefits**: Type safety, automatic validation, clear data contracts

#### **3. Services Module (`src/services/`)**
- **Purpose**: External API integrations
- **Key Components**:
  - `openai_service.py`: OpenAI API interactions (router, query generation, mapping)
  - `perplexity_service.py`: Perplexity AI search integration
- **Benefits**: Encapsulated external dependencies, easy testing, reusability

#### **4. API Module (`src/api/`)**
- **Purpose**: FastAPI server and endpoints
- **Key Components**:
  - `server.py`: FastAPI app configuration and middleware
  - `endpoints.py`: API route handlers
- **Benefits**: Clean API layer, easy to extend with new endpoints

#### **5. Config Module (`src/config/`)**
- **Purpose**: Application configuration and prompts
- **Key Components**:
  - `settings.py`: API keys, model configurations, tools
  - `prompts.py`: AI system prompts and instructions
- **Benefits**: Centralized configuration, easy to modify prompts

#### **6. Utils Module (`src/utils/`)**
- **Purpose**: Helper functions and utilities
- **Key Components**:
  - `helpers.py`: Common utility functions
- **Benefits**: Reusable code, clean separation of utilities

#### **7. Database Module (`database/`) - NEW**
- **Purpose**: Complete database functionality and persistence
- **Key Components**:
  - `services/`: Database service layer with core operations
  - `api/`: Database-specific REST endpoints
  - `models.py`: SQLAlchemy ORM models
  - `schema.sql`: Database schema definitions
- **Benefits**: Persistent storage, analytics, session management, LLM integration

## 🔄 Workflow Types

The system supports two main research workflows:

### 1. Provide_a_List Workflow
- **Purpose**: Generate comprehensive lists of certifications and requirements
- **Use Case**: "What certifications do I need to export X to Y?"
- **Output**: Structured certification data with legal references

### 2. Search_the_Internet Workflow
- **Purpose**: General research and information gathering
- **Use Case**: "How does the certification process work?"
- **Output**: Detailed explanations and procedures

## 🧠 Intelligent Features

### Smart Query Mapping
- **Metadata-Driven**: Uses rich domain metadata for intelligent website selection
- **Geographic Matching**: Automatically matches queries to relevant regional authorities
- **Industry Specialization**: Routes queries to specialized industry websites
- **Keyword Optimization**: Uses boost keywords for precise matching

### Chat History Integration
- **Context Awareness**: Incorporates previous conversation context
- **Query Enhancement**: Builds upon previous research questions
- **Continuity**: Maintains conversation flow across multiple requests

### Structured Output
- **Pydantic Models**: Type-safe structured responses
- **OpenAI Integration**: Uses modern `text_format` for reliable parsing
- **Perplexity Integration**: JSON schema-based structured output

### Database Integration - NEW
- **Persistent Storage**: All conversations and research stored in PostgreSQL
- **Session Management**: Multi-user session support with conversation history
- **Analytics**: Comprehensive tracking of user interactions and performance
- **LLM Context**: Enhanced context retrieval for better responses
- **Performance Monitoring**: Real-time performance tracking and optimization

## 📡 API Endpoints

### Main Research Endpoint
- **`POST /research`**: Primary research endpoint with domain metadata and chat history

### Database Endpoints - NEW
- **`GET /db/health`**: Database health check
- **`POST /db/sessions/create`**: Create new chat session
- **`GET /db/sessions/{session_id}`**: Get session information
- **`POST /db/messages/store`**: Store chat message
- **`GET /db/messages/{session_id}/recent`**: Get recent messages for context
- **`POST /db/research/store`**: Store research request
- **`GET /db/research/history/{session_id}`**: Get research history
- **`GET /db/context/{session_id}`**: Get comprehensive research context
- **`POST /db/analytics/log`**: Log analytics events

### Supporting Endpoints
- **`GET /health`**: Health check
- **`GET /sessions/{session_id}/messages`**: Chat history retrieval
- **`GET /sessions/{session_id}/research-history`**: Research history
- **`POST /sessions`**: Session creation

## 💡 Key Strengths

1. **Intelligent Routing**: AI-powered decision making for workflow selection
2. **Scalable Architecture**: Modular design allows easy extension
3. **Rich Metadata**: Comprehensive domain information for precise targeting
4. **Parallel Processing**: Efficient concurrent search execution
5. **Structured Output**: Type-safe, reliable data formats
6. **Context Awareness**: Chat history integration for better responses
7. **Comprehensive Logging**: Full audit trail and analytics
8. **Database Integration**: Persistent storage and session management
9. **Performance Monitoring**: Real-time analytics and optimization
10. **Clean Organization**: Well-structured codebase with clear separation of concerns

## 🔍 Areas for Enhancement

1. **Authentication**: User authentication and authorization
2. **Rate Limiting**: API rate limiting for external services
3. **Caching**: Result caching for repeated queries
4. **Advanced Analytics**: More sophisticated analytics and reporting
5. **Multi-tenancy**: Support for multiple organizations
6. **Real-time Features**: WebSocket connections for live updates

## 🎯 Use Cases

This system is ideal for:
- **Manufacturers** seeking export compliance information
- **Compliance Managers** researching regulatory requirements
- **Exporters** understanding certification needs
- **Consultants** providing regulatory guidance
- **Small-to-medium businesses** navigating global trade requirements

## 🧪 Testing

### Run All Tests
```bash
# API tests
python tests/test_api_client.py

# Database integration tests
python test_database_integration.py

# Structured output tests
python tests/test_structured_output.py
```

### Database Testing
```bash
# Test database connection and operations
python test_database_integration.py

# Test specific database endpoints
curl http://localhost:8000/db/health
```

## 📚 Documentation

- **Main Documentation**: This README
- **Database Integration**: `DATABASE_INTEGRATION.md`
- **Database Module**: `database/README.md`
- **API Documentation**: Available at `/docs` when running the server

The codebase demonstrates excellent software engineering practices with clean architecture, comprehensive error handling, intelligent AI integration, and robust database functionality for a specialized domain. 