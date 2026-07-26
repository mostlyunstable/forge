# Forge API Reference

## Conversations API

### Start a Conversation Session
**Endpoint**: `POST /api/conversations/start`
**Status Code**: `201 Created`

**Description**: Starts a new conversational session and associates it with a given project. It manages the underlying conversational aggregate root.

**Request Body**:
```json
{
  "project_id": "string (UUID)",
  "title": "string (Optional, defaults to 'New Conversation')"
}
```

**Response Body**:
```json
{
  "conversation_id": "string (UUID)",
  "project_id": "string (UUID)",
  "title": "string"
}
```

### Send a Message
**Endpoint**: `POST /api/conversations/{conversation_id}/messages`
**Status Code**: `200 OK`

**Description**: Sends a message to a specific conversation, retrieves contextual information (code, decisions, bugs), constructs the conversation context, and uses the Reasoning Engine to generate a grounded response with citations.

**Path Parameters**:
- `conversation_id`: The ID of the conversation to post the message to.

**Request Body**:
```json
{
  "message": "string"
}
```

**Response Body**:
```json
{
  "conversation_id": "string (UUID)",
  "response": "string",
  "citations": [
    {
      "source": "string (File path or title)",
      "content": "string (Context content)",
      "score": "float (Relevance score)"
    }
  ]
}
```
