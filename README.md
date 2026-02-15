# Chat Application with Analytics

A modern chat application with analytics capabilities, built using React, FastAPI, and LangGraph for advanced conversation handling.

## Solution Architecture Overview

### Frontend Architecture
- **React with TypeScript**: Ensures type safety and better developer experience
- **Component Structure**:
  - `Chat`: Main chat interface with real-time message handling
  - `Analytics`: Dashboard for monitoring chat metrics and performance
- **State Management**: Uses React hooks for local state management
- **Routing**: React Router for navigation between chat and analytics views
- **API Integration**: Axios for HTTP requests to the backend

### Backend Architecture
- **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- **Middleware**:
  - CORS handling for frontend communication
  - Correlation ID tracking for request tracing
- **API Routes**:
  - `/api/chat/message`: Process and respond to chat messages
  - `/api/chat/history`: Retrieve chat history
- **Logging**: Structured logging with correlation IDs for better debugging

## Architectural Reasoning

### LangGraph Component Architecture
1. **Workflow Organization**
   - **Decision**: Modular subgraph approach
   - **Why**: Enables independent testing, maintenance, and scaling of conversation components
   - **Implementation**: 
     - `conversation.py`: Core chat logic
     - `guardrail.py`: Content filtering and safety checks
     - `main.py`: Workflow orchestration

2. **State Management**
   - **Decision**: Pydantic models for state transitions
   - **Why**: Type safety and validation at each step of the conversation
   - **Components**:
     - Message validation
     - Context preservation
     - History tracking

### Database Architecture
1. **Current Implementation**
   - **Decision**: In-memory storage with CSV backup
   - **Why**: 
     - Quick prototyping
     - No complex relationships needed yet
     - Easy data portability
   - **Tradeoffs**:
     - Limited scalability
     - No concurrent write handling

2. **Explored Options**:
   - **SQLite**:
     - Pros: Simple, file-based, ACID compliant
     - Cons: Limited concurrency, single-writer
   - **PostgreSQL**:
     - Pros: Robust, scalable, concurrent
     - Cons: Overhead for simple chat storage
   - **MongoDB**:
     - Pros: Flexible schema, good for chat logs
     - Cons: Eventual consistency might affect chat order

3. **Future Considerations**:
   - Migration path to PostgreSQL when needed
   - Redis for caching frequent requests
   - Message queue for async processing

### Key Features and Reasoning
1. **Real-time Chat**:
   - Instant message display
   - Automatic URL detection and formatting
   - Loading states and error handling
   - Message history persistence

2. **Analytics Dashboard**:
   - Conversation statistics
   - User engagement metrics
   - System performance monitoring
   - Real-time data updates

3. **Developer Experience**:
   - TypeScript for type safety
   - Structured error handling
   - Comprehensive logging
   - Clean code architecture

## Quick Start Guide

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Installation and Running


1. **Backend Setup**:
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/MacOS

# Install dependencies and start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3. **Frontend Setup**:
```bash
# Open a new terminal
cd frontend
npm install
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Project Structure
```
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── types/         # TypeScript interfaces
│   │   └── App.tsx        # Main application component
│   └── package.json
│
└── backend/                # FastAPI backend application
    ├── app/
    │   ├── routers/       # API route handlers
    │   ├── schemas/       # Pydantic models
    │   ├── middleware/    # Custom middleware
    │   ├── workflows/     # LangGraph components
    │   │   ├── main.py           # Main workflow
    │   │   └── subgraphs/        # Modular components
    │   │       ├── conversation.py
    │   │       └── guardrail.py
    │   └── main.py       # Application entry point
    └── requirements.txt
```

### Development Workflow
1. Start the backend server (from `/backend` directory):
```bash
uvicorn app.main:app --reload --port 8000
```

2. Start the frontend development server (from `/frontend` directory):
```bash
npm start
```

3. Access the application:
   - Chat Interface: http://localhost:3000
   - Analytics Dashboard: http://localhost:3000/analytics
   - API Documentation: http://localhost:8000/docs

### API Endpoints
- `POST /api/chat/message`: Send a chat message
- `GET /api/chat/history`: Retrieve chat history

### Future Enhancements
1. **Database Migration**:
   - Implement PostgreSQL for scalability
   - Add Redis caching layer
   - Message queue for async operations

2. **LangGraph Improvements**:
   - Additional conversation subgraphs
   - Enhanced context management
   - Custom node implementations

3. **System Features**:
   - User authentication
   - Real-time WebSocket communication
   - Advanced analytics with data visualization
   - Customizable chat interface themes

Architectural Reasoning:

For Backend, FAST API was selected for it's reliability. Then a decomoposer module is added, to seprate out intents from a user query, Intents could be chattng, web_search, csv_operations. The decomposer module genrates a task graph which specifies the order of execution, This is then sent to Langraph workflow. The langgraph workflow is hierarchial orchestration. With this approach we can add multiple sub agents working on specific tasks. The controller node is the task schedular, and all agents share the same agent_state. A retry module is also added if tasks fail, giving a chance for recovery.
