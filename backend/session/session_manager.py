import json
import redis
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict] = {}

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    preferences: Dict = {}
    intents: List[str] = []

class SessionManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_timeout = 3600  # 1 hour
    
    def create_session(self, user_id: str, user_profile: UserProfile) -> str:
        """Create a new session for a user"""
        session_id = f"session:{user_id}:{datetime.now().timestamp()}"
        
        session_data = {
            "user_profile": user_profile.dict(),
            "conversation_history": [],
            "context": {},
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        # Store in Redis with expiration
        self.redis.setex(
            session_id,
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        session_data = self.redis.get(session_id)
        
        if session_data:
            # Refresh TTL on access
            self.redis.expire(session_id, self.session_timeout)
            return json.loads(session_data)
        
        return None
    
    def update_conversation(self, session_id: str, message: Message):
        """Add a message to conversation history"""
        session_data = self.get_session(session_id)
        
        if session_data:
            session_data["conversation_history"].append(message.dict())
            session_data["last_activity"] = datetime.now().isoformat()
            
            self.redis.setex(
                session_id,
                self.session_timeout,
                json.dumps(session_data)
            )
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent conversation history"""
        session_data = self.get_session(session_id)
        
        if session_data:
            history = session_data["conversation_history"][-limit:]
            return [Message(**msg) for msg in history]
        
        return []
    
    def update_context(self, session_id: str, context_key: str, context_value: any):
        """Update session context"""
        session_data = self.get_session(session_id)
        
        if session_data:
            session_data["context"][context_key] = context_value
            session_data["last_activity"] = datetime.now().isoformat()
            
            self.redis.setex(
                session_id,
                self.session_timeout,
                json.dumps(session_data)
            )
    
    def get_context(self, session_id: str) -> Dict:
        """Get full session context"""
        session_data = self.get_session(session_id)
        return session_data.get("context", {}) if session_data else {}
    
    def detect_intent(self, user_query: str) -> str:
        """Simple intent detection"""
        # In production, use NLP models
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["search", "find", "look for"]):
            return "search"
        elif any(word in query_lower for word in ["create", "make", "generate"]):
            return "create"
        elif any(word in query_lower for word in ["update", "modify", "change"]):
            return "update"
        elif any(word in query_lower for word in ["delete", "remove"]):
            return "delete"
        elif any(word in query_lower for word in ["analyze", "report", "dashboard"]):
            return "analyze"
        else:
            return "query"
    
    def end_session(self, session_id: str):
        """End a session"""
        self.redis.delete(session_id)