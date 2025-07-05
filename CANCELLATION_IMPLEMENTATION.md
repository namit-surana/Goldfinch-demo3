# Cancellation Implementation Guide

## 🎯 Overview

This implementation adds comprehensive "stop generation" functionality to the Internal_testing Demo3 TIC Research chatbot. Users can now cancel ongoing research requests at any point during the process.

## 🗃️ Database Changes

### New Tables
- **`cancellation_tokens`** - Tracks active cancellation tokens for real-time cancellation
- **Added fields to `research_requests`**:
  - `cancellation_requested` - Boolean flag
  - `cancellation_timestamp` - When cancellation was requested
  - `cancellation_reason` - Reason for cancellation
  - `partial_results` - JSON of partial results if cancelled mid-process
  - `completed_queries` - Number of completed queries
  - `total_queries` - Total number of planned queries

### Migration Required
Run the SQL script: `database/schema_updates.sql`

## 🛠️ Code Components

### 1. Cancellation Manager (`src/utils/cancellation_manager.py`)
- **`CancellationManager`** - Central manager for all cancellation tokens
- **`CancellationToken`** - Context manager for individual requests
- **`CancellationException`** - Custom exception for cancellation events

### 2. Database Service Updates
- **`create_cancellation_token()`** - Creates new token
- **`cancel_token()`** - Marks token as cancelled
- **`is_request_cancelled()`** - Checks cancellation status
- **`update_partial_results()`** - Saves partial results

### 3. API Endpoints
- **`POST /chat/cancel`** - Cancel specific request or all requests in session
- **`GET /chat/active_requests/{session_id}`** - Get active requests for session
- **Modified `/chat/stream_summary`** - Now supports cancellation

### 4. Workflow Updates
- **`route_research_request_with_progress()`** - Cancellation-aware routing
- **`execute_workflow_with_progress()`** - Handles partial results on cancellation

## 🔗 API Usage

### Cancel a Specific Request
```bash
curl -X POST http://localhost:8000/chat/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "request_123",
    "reason": "User requested cancellation"
  }'
```

### Cancel All Requests in Session
```bash
curl -X POST http://localhost:8000/chat/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_456",
    "reason": "Session cancelled"
  }'
```

### Get Active Requests
```bash
curl http://localhost:8000/chat/active_requests/session_456
```

## 🌐 Frontend Integration

### Basic Setup
```javascript
let currentRequestId = null;
let isGenerating = false;

// Start request
async function sendMessage() {
    const response = await fetch('/chat/stream_summary', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            content: userMessage
        })
    });
    
    // Process streaming response
    const reader = response.body.getReader();
    // ... handle streaming data
}

// Cancel request
async function stopGeneration() {
    if (!currentRequestId) return;
    
    await fetch('/chat/cancel', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            request_id: currentRequestId,
            reason: 'User requested cancellation'
        })
    });
}
```

### Stream Data Types
- **`request_created`** - New request started, provides `request_id`
- **`status`** - Progress updates
- **`search_progress`** - Search-specific progress
- **`summary_chunk`** - Streaming response content
- **`cancelled`** - Request was cancelled
- **`completed`** - Request completed successfully

## 🔄 Cancellation Flow

### 1. User Cancellation Process
1. User clicks "Stop" button
2. Frontend sends POST to `/chat/cancel`
3. Backend marks cancellation token as cancelled
4. Active workflow checks token and throws `CancellationException`
5. System returns partial results if available
6. Database updated with cancellation details

### 2. Graceful Cancellation Strategy
- **Immediate** - Direct responses stop immediately
- **Soft Stop** - Complete current searches, skip remaining ones
- **Partial Results** - Return completed work with "cancelled" status
- **Database Consistency** - Always update request status

## 📊 Cancellation Scenarios

### 1. During Router Decision (Fast)
- Quick cancellation, minimal resources used
- Direct response with cancellation message

### 2. During Search Generation (Medium)
- Cancellation before searches start
- No external API calls wasted

### 3. During Parallel Searches (Complex)
- Complete ongoing searches, cancel pending ones
- Return partial results with clear indication
- Update database with completion status

### 4. During Summary Generation (Streaming)
- Stop summary generation mid-stream
- Return partial summary if useful
- Clean up OpenAI streaming connection

## 🎨 User Experience

### Visual Feedback
- **Progress Bar** - Shows current progress
- **Stop Button** - Enabled only when generation is active
- **Status Messages** - Clear indication of current state
- **Cancellation Confirmation** - Immediate feedback on cancellation

### Error Handling
- **Graceful Degradation** - Partial results when possible
- **Clear Messages** - User-friendly error messages
- **State Management** - Consistent UI state after cancellation

## 🔧 Testing

### Manual Testing
1. Start the API server: `python start_api.py`
2. Open `frontend_example.html` in browser
3. Send a research request
4. Click "Stop" button during processing
5. Verify cancellation message and partial results

### API Testing
```bash
# Test cancellation endpoint
curl -X POST http://localhost:8000/chat/cancel \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session", "reason": "test"}'

# Test active requests endpoint
curl http://localhost:8000/chat/active_requests/test_session
```

## 🚀 Deployment Considerations

### Environment Variables
- Ensure all existing environment variables are set
- Database credentials for schema updates
- API keys for OpenAI and Perplexity

### Database Migration
```sql
-- Run the schema updates
\i database/schema_updates.sql
```

### Monitoring
- Track cancellation rates in analytics
- Monitor partial result quality
- Watch for resource cleanup issues

## 🔒 Security Considerations

### Token Management
- Tokens are session-scoped
- Automatic cleanup on completion
- No sensitive data in tokens

### Request Validation
- Validate session ownership
- Prevent unauthorized cancellations
- Rate limiting on cancellation endpoints

## 📈 Performance Impact

### Memory Usage
- Minimal overhead for cancellation tokens
- Automatic cleanup prevents memory leaks
- Efficient lookup using indexed fields

### Response Times
- Cancellation is near-instantaneous
- Partial results reduce wasted computation
- Database updates are lightweight

## 🛡️ Error Handling

### Cancellation Exceptions
- Custom `CancellationException` for clear error flow
- Graceful handling in all workflow stages
- Proper resource cleanup in finally blocks

### Database Errors
- Rollback on cancellation token creation failure
- Consistent state even on partial failures
- Detailed error logging for debugging

## 📝 Best Practices

### Frontend Implementation
1. **Always check request status** before allowing new requests
2. **Provide clear visual feedback** during cancellation
3. **Handle partial results gracefully** with user-friendly messages
4. **Implement proper cleanup** for streaming connections

### Backend Implementation
1. **Check cancellation frequently** in long-running operations
2. **Save partial results** when possible for user value
3. **Use proper exception handling** for cancellation flow
4. **Update database consistently** regardless of cancellation timing

This implementation provides a robust, user-friendly cancellation system that maintains data integrity while providing excellent user experience. 