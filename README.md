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
├── 📁 tests/                        # Test files
│   ├── test_api_client.py           # API client tests
│   └── test_structured_output.py    # Structured output tests
├── 🐍 start_api.py                  # Application entry point
├── 📄 requirements.txt              # Python dependencies
├── 📄 render.yaml                   # Render deployment configuration
├── 📄 .env.example                  # Environment variables template
└── 📄 README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Perplexity AI API key

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
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the API server**
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

## 📡 API Endpoints

### POST `/research`

Main research endpoint that processes TIC-related queries.

**Request Body:**
```json
{
  "research_question": "What certifications are needed to export electronics to the EU?",
  "domain_list_metadata": [
    {
      "name": "FDA",
      "domain": "fda.gov",
      "region": "US",
      "org_type": "Regulatory Body",
      "industry_tags": ["food", "drugs", "medical devices"],
      "semantic_profile": "US Food and Drug Administration...",
      "boost_keywords": ["FDA approval", "food safety"],
      "aliases": ["Food and Drug Administration"]
    }
  ],
  "chat_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "status": "completed",
  "research_question": "Original question",
  "workflow_type": "Provide_a_List",
  "search_results": [...],
  "query_mappings": [...],
  "execution_summary": {...},
  "timestamp": "2024-01-01T00:00:00",
  "processing_time": 15.5
}
```

### GET `/health`

Health check endpoint to verify API status.

### GET `/`

Root endpoint with API information.

## 🧪 Testing

### Run Tests
```bash
# API client tests
python tests/test_api_client.py

# Structured output tests
python tests/test_structured_output.py
```

### Postman Collection
Import `TIC_Research_API.postman_collection.json` for API testing.

## 🚀 Deployment

### Local Development
```bash
python start_api.py
```

### Production Deployment
The project includes `render.yaml` for easy deployment on Render:

1. Connect your repository to Render
2. Set environment variables
3. Deploy automatically

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

### API Configuration

The system uses the following default configuration:

- **OpenAI Model**: `gpt-4o-2024-08-06`
- **Perplexity Model**: `sonar-pro`
- **Temperature**: 0.1 (for consistent results)

## 📚 Benefits of Modular Architecture

### **1. Maintainability**
- Clear separation of concerns
- Easy to locate and modify specific functionality
- Reduced code coupling

### **2. Testability**
- Each module can be tested independently
- Mock external dependencies easily
- Clear interfaces for unit testing

### **3. Scalability**
- Easy to add new services or workflows
- Modular design supports horizontal scaling
- Clear extension points

### **4. Reusability**
- Services can be reused across different workflows
- Models provide consistent data structures
- Utilities are shared across the application

### **5. Development Experience**
- Clear project structure for new developers
- Intuitive import paths
- Easy to understand code organization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the modular structure
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is proprietary software developed by Mangrove AI Inc.

## 🆘 Support

For support and questions:
- Check the documentation in the `docs/` folder
- Review the Postman collection for API examples
- Contact the development team

---

**Built with ❤️ by Mangrove AI** 