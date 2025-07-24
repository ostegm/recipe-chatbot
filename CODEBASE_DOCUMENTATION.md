# Recipe Chatbot - Comprehensive Codebase Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [System Architecture Diagram](#system-architecture-diagram)
5. [Core Components](#core-components)
6. [Data Flow](#data-flow)
7. [Directory Structure](#directory-structure)
8. [Key Features](#key-features)
9. [Educational Structure](#educational-structure)
10. [Deployment & Configuration](#deployment--configuration)

## Project Overview

The Recipe Chatbot is an educational AI-powered conversational system designed for learning AI evaluation techniques. It serves as a practical platform for a comprehensive course on evaluating and improving AI systems. The chatbot provides recipe recommendations through a web interface while maintaining conversation history and supporting various evaluation methodologies.

### Purpose
- **Primary**: Educational platform for AI evaluation techniques
- **Secondary**: Functional recipe recommendation system
- **Focus**: Systematic evaluation over implementation

## Architecture Overview

The system follows a modular, three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                   (HTML/CSS/JavaScript)                      │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API Layer                       │
│                         (FastAPI)                            │
│  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │   Main    │  │     LLM      │  │    Retrieval      │   │
│  │  Server   │  │ Integration  │  │     System        │   │
│  └───────────┘  └──────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│         (JSON files, CSV datasets, Trace logs)              │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Technologies
- **Python 3.x**: Core programming language with type hints
- **FastAPI**: Modern, async web framework for building APIs
- **LiteLLM**: Unified interface for multiple LLM providers (OpenAI, Anthropic, etc.)
- **BM25 (rank-bm25)**: Information retrieval algorithm for recipe search
- **Pydantic**: Data validation and settings management
- **uvicorn**: ASGI server for running FastAPI

### Frontend Technologies
- **HTML5/CSS3**: Semantic markup and modern styling
- **Vanilla JavaScript**: No framework dependencies
- **Marked.js**: Markdown rendering for rich text responses
- **Google Fonts (Inter)**: Modern typography

### Data Processing & Analysis
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning utilities
- **Matplotlib/Seaborn/Plotly**: Data visualization

### Development Tools
- **python-dotenv**: Environment variable management
- **Rich/TQDM**: Terminal UI enhancements
- **Concurrent.futures**: Parallel processing

## System Architecture Diagram

```
┌──────────────────┐     ┌──────────────────────────────────┐
│   Web Browser    │     │         Recipe Chatbot           │
│                  │     │                                  │
│  ┌────────────┐  │     │  ┌──────────────────────────┐  │
│  │  Chat UI   │◀─┼─────┼─▶│    FastAPI Server        │  │
│  │ (index.html│  │     │  │    (main.py)             │  │
│  └────────────┘  │     │  └──────────┬───────────────┘  │
└──────────────────┘     │             │                   │
                         │             ▼                   │
                         │  ┌──────────────────────────┐  │
                         │  │   LLM Integration       │  │
                         │  │   (utils.py)            │  │
                         │  │  ┌─────────────────┐    │  │
                         │  │  │  System Prompt  │    │  │
                         │  │  └─────────────────┘    │  │
                         │  └──────────┬───────────────┘  │
                         │             │                   │
                         │             ▼                   │
                         │  ┌──────────────────────────┐  │
                         │  │   External LLM APIs     │  │
                         │  │  (OpenAI, Anthropic)    │  │
                         │  └──────────────────────────┘  │
                         │                                 │
                         │  ┌──────────────────────────┐  │
                         │  │  Recipe Retrieval       │  │
                         │  │  (retrieval.py)         │  │
                         │  │  ┌─────────────────┐    │  │
                         │  │  │   BM25 Index    │    │  │
                         │  │  └─────────────────┘    │  │
                         │  └──────────┬───────────────┘  │
                         │             │                   │
                         │             ▼                   │
                         │  ┌──────────────────────────┐  │
                         │  │  Query Enhancement      │  │
                         │  │  (query_rewrite_agent)  │  │
                         │  └──────────────────────────┘  │
                         │                                 │
                         │  ┌──────────────────────────┐  │
                         │  │    Data Storage         │  │
                         │  │  • Recipe JSON          │  │
                         │  │  • Trace Logs           │  │
                         │  │  • Evaluation Data      │  │
                         │  └──────────────────────────┘  │
                         └─────────────────────────────────┘
```

## Core Components

### 1. Backend API (`backend/main.py`)
The FastAPI application serves as the main entry point:

```python
# Key endpoints
POST /chat          # Main chat interface
GET /               # Serves frontend HTML
GET /static/*       # Static file serving
```

**Features:**
- Request/response validation with Pydantic models
- Automatic trace logging for all conversations
- CORS support for cross-origin requests
- Static file serving for frontend

### 2. LLM Integration (`backend/utils.py`)
Handles all language model interactions:

```python
def get_agent_response(messages: List[Dict[str, str]]) -> str:
    # Configurable model selection
    # System prompt injection
    # Conversation history management
```

**System Prompt:**
- Expert chef persona
- One recipe at a time
- Assumes basic ingredients
- Includes serving sizes
- Avoids follow-up questions

### 3. Recipe Retrieval System (`backend/retrieval.py`)
BM25-based search engine with persistence:

```python
class RecipeRetriever:
    def build_index(self)      # Creates BM25 index
    def retrieve_bm25(query)   # Returns top-k recipes
    def save_index(path)       # Persists index
    def load_index(path)       # Loads saved index
```

**Indexing Strategy:**
- Combines: name, description, ingredients, steps, tags
- Text preprocessing: lowercase, tokenization
- Supports pickle serialization

### 4. Query Enhancement (`backend/query_rewrite_agent.py`)
LLM-powered query optimization:

```python
class QueryRewriteAgent:
    # Three strategies:
    1. extract_keywords()    # Key cooking terms
    2. rewrite_query()      # Natural → search-friendly
    3. expand_query()       # Add synonyms/related terms
```

**Features:**
- Parallel processing with ThreadPoolExecutor
- Retry logic with exponential backoff
- Multiple strategy support

### 5. Evaluation Framework (`backend/evaluation_utils.py`)
Comprehensive evaluation tools:

```python
class BaseRetrievalEvaluator:
    # Metrics:
    - Recall@k (k=1,3,5,10)
    - Mean Reciprocal Rank (MRR)
    - Found/not found counts
    - Average/median ranks
```

## Data Flow

### 1. User Interaction Flow
```
User Input
    │
    ▼
Frontend Validation
    │
    ▼
POST /chat (with conversation history)
    │
    ▼
Backend Validation (Pydantic)
    │
    ▼
Trace Logging (JSON)
    │
    ▼
LLM Processing
    │
    ├─► System Prompt Injection
    ├─► Context Management
    └─► Response Generation
    │
    ▼
Response Formatting
    │
    ▼
Frontend Rendering (Markdown)
    │
    ▼
Update Chat History
```

### 2. Retrieval Flow (when enabled)
```
User Query
    │
    ▼
Query Enhancement (optional)
    │
    ├─► Keyword Extraction
    ├─► Query Rewriting
    └─► Query Expansion
    │
    ▼
BM25 Retrieval
    │
    ▼
Ranking & Scoring
    │
    ▼
Top-k Results
    │
    ▼
LLM Context Injection
```

## Directory Structure

```
recipe-chatbot/
├── backend/                    # Core application logic
│   ├── __init__.py            # Package initialization
│   ├── main.py                # FastAPI server
│   ├── utils.py               # LLM integration
│   ├── retrieval.py           # BM25 search engine
│   ├── query_rewrite_agent.py # Query optimization
│   └── evaluation_utils.py    # Evaluation metrics
│
├── frontend/                   # Web UI
│   └── index.html             # Single-page application
│
├── annotation/                 # Manual evaluation tool
│   ├── annotation.py          # FastHTML annotation interface
│   └── traces/                # Saved conversation logs
│
├── homeworks/                  # Educational assignments
│   ├── hw1/                   # Prompt engineering basics
│   ├── hw2/                   # Error analysis & taxonomy
│   ├── hw3/                   # LLM-as-Judge evaluation
│   ├── hw4/                   # RAG/Retrieval evaluation
│   └── hw5/                   # Agent failure analysis
│
├── data/                       # Datasets
│   └── sample_queries.csv     # Test queries
│
├── scripts/                    # Utility scripts
│   └── bulk_test.py          # Batch testing tool
│
├── requirements.txt           # Python dependencies
├── env.example               # Environment template
└── README.md                 # Project documentation
```

## Key Features

### 1. Conversation Management
- Full conversation history tracking
- Automatic trace saving with timestamps
- Session persistence across requests

### 2. Flexible LLM Support
- Multiple provider support via LiteLLM
- Easy model switching via environment variables
- Fallback to default models

### 3. Advanced Retrieval
- BM25 ranking algorithm
- Multi-field indexing
- Persistent index caching
- Query preprocessing

### 4. Comprehensive Evaluation
- Standard IR metrics (Recall, MRR)
- System comparison tools
- Automated evaluation pipelines
- Manual annotation interface

### 5. Educational Design
- Progressive homework structure
- Interactive walkthroughs
- Video tutorials
- Real-world evaluation techniques

## Educational Structure

The project follows a carefully designed learning path:

### Homework 1: Prompt Engineering
- **Goal**: Learn basic prompt optimization
- **Tools**: Simple prompt testing framework
- **Outcome**: Understanding prompt impact on performance

### Homework 2: Error Analysis
- **Goal**: Systematic failure analysis
- **Methods**: Open coding, axial coding
- **Tools**: Error taxonomy development
- **Outcome**: Structured error categorization

### Homework 3: LLM-as-Judge
- **Goal**: Automated evaluation systems
- **Tools**: Judgy library integration
- **Methods**: Judge prompt development
- **Outcome**: Scalable evaluation pipeline

### Homework 4: Retrieval Evaluation
- **Goal**: Information retrieval assessment
- **Tools**: BM25, query enhancement
- **Metrics**: Recall@k, MRR
- **Outcome**: Enhanced retrieval system

### Homework 5: Agent Analysis
- **Goal**: Complex behavior analysis
- **Tools**: Trace analysis, visualization
- **Methods**: State transition analysis
- **Outcome**: Deep understanding of agent failures

## Deployment & Configuration

### Environment Variables (.env)
```bash
# LLM Configuration
MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Other providers supported via LiteLLM
```

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your API keys

# Run the server
cd backend
python main.py

# Access at http://localhost:8000
```

### Development Best Practices
1. **Type Hints**: Use throughout for better IDE support
2. **Pydantic Models**: Validate all API inputs/outputs
3. **Async Support**: Leverage FastAPI's async capabilities
4. **Error Handling**: Comprehensive exception handling
5. **Logging**: Trace all interactions for debugging
6. **Testing**: Use evaluation framework for systematic testing

## Conclusion

The Recipe Chatbot is a well-architected educational platform that demonstrates professional software engineering practices while serving as an effective learning tool for AI evaluation. Its modular design, comprehensive evaluation framework, and progressive learning structure make it an excellent resource for understanding real-world AI system evaluation.

The combination of modern web technologies, flexible LLM integration, and sophisticated retrieval systems provides a solid foundation for both learning and practical application development.