from openai import OpenAI
from typing import Dict, List, Optional
from datetime import datetime
import json
import asyncio

class Orchestrator:
    def __init__(self, api_key: str):
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Use GPT-4o (recommended) or GPT-3.5-turbo
        self.model = "gpt-4o"  # Options: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
        
        # Configure generation settings
        self.temperature = 0.7
        self.max_tokens = 2000
        
        # Available actions/tools
        self.available_actions = {
            "search_database": self.search_database,
            "query_sql": self.query_sql,
            "create_document": self.create_document,
            "analyze_data": self.analyze_data,
            "get_recommendations": self.get_recommendations
        }
    
    async def plan_and_execute(
        self,
        user_query: str,
        context: Dict,
        conversation_history: List[Dict],
        user_permissions: List[str]
    ) -> Dict:
        """
        Main orchestration method:
        1. Analyze user query and context
        2. Create execution plan
        3. Check permissions
        4. Execute actions
        5. Return results
        """
        
        try:
            # Step 1: Create execution plan
            plan = await self._create_plan(user_query, context, conversation_history)
            
            # Step 2: Validate permissions
            if not self._check_permissions(plan, user_permissions):
                return {
                    "success": False,
                    "error": "Insufficient permissions for requested action",
                    "required_permissions": plan.get("required_permissions", [])
                }
            
            # Step 3: Execute plan
            results = await self._execute_plan(plan, context)
            
            # Step 4: Generate response
            response = await self._generate_response(user_query, results, conversation_history)
            
            return {
                "success": True,
                "response": response,
                "plan": plan,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in plan_and_execute: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Orchestration error: {str(e)}",
                "response": "I apologize, but I encountered an error processing your request. Please try again."
            }
    
    async def _create_plan(
        self,
        user_query: str,
        context: Dict,
        history: List[Dict]
    ) -> Dict:
        """Use GPT to analyze query and create execution plan"""
        
        try:
            # Build messages for OpenAI
            messages = []
            
            # System message with instructions
            system_message = {
                "role": "system",
                "content": """You are an AI assistant that creates execution plans for user queries.

Available Actions:
- search_database: Search unstructured data (documents, FAQs)
- query_sql: Query structured data (CRM, SQL databases)
- create_document: Create new documents or records
- analyze_data: Perform data analysis
- get_recommendations: Get AI recommendations

Create a JSON plan with this exact structure:
{
    "intent": "user's intent (search/create/update/delete/analyze/query)",
    "actions": ["list", "of", "actions", "to", "execute"],
    "parameters": {"action_name": {"param": "value"}},
    "required_permissions": ["permission1", "permission2"]
}

Return ONLY the JSON object, no additional text or markdown formatting."""
            }
            messages.append(system_message)
            
            # Add conversation history (last 5 messages)
            for msg in history[-5:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current query with context
            user_message = f"""User Query: {user_query}

Context: {json.dumps(context, indent=2)}

Create an execution plan for this query."""
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call OpenAI API (synchronous call wrapped in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )
            )
            
            plan_text = response.choices[0].message.content
            
            # Extract JSON from response
            start_idx = plan_text.find('{')
            end_idx = plan_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                plan = json.loads(plan_text[start_idx:end_idx])
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            # Fallback if parsing fails
            print(f"Plan creation error: {e}")
            plan = {
                "intent": "query",
                "actions": ["search_database"],
                "parameters": {},
                "required_permissions": ["read"]
            }
        
        return plan
    
    def _check_permissions(self, plan: Dict, user_permissions: List[str]) -> bool:
        """Check if user has required permissions"""
        required = plan.get("required_permissions", [])
        return all(perm in user_permissions for perm in required)
    
    async def _execute_plan(self, plan: Dict, context: Dict) -> Dict:
        """Execute the planned actions"""
        results = {}
        
        for action in plan.get("actions", []):
            if action in self.available_actions:
                params = plan.get("parameters", {}).get(action, {})
                params["context"] = context
                
                try:
                    result = await self.available_actions[action](params)
                    results[action] = result
                except Exception as e:
                    results[action] = {"error": str(e)}
        
        return results
    
    async def _generate_response(
        self,
        user_query: str,
        execution_results: Dict,
        history: List[Dict]
    ) -> str:
        """Generate natural language response from execution results"""
        
        try:
            # Build messages
            messages = []
            
            # System message
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses based on the execution results."
            })
            
            # Add conversation history (last 5 messages)
            for msg in history[-5:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current query with results
            user_message = f"""User Query: {user_query}

Execution Results:
{json.dumps(execution_results, indent=2)}

Provide a helpful, natural response that answers the user's question based on these results."""
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call OpenAI API (synchronous call wrapped in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Response generation error: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    # Action implementations
    async def search_database(self, params: Dict) -> Dict:
        """Search unstructured data"""
        # In production: integrate with vector DB or search engine
        return {
            "results": [
                "Company Handbook - Section 3: Employee Benefits",
                "Q3 Financial Report - Executive Summary",
                "HR Policy Document - Remote Work Guidelines"
            ],
            "count": 3,
            "source": "document_database"
        }
    
    async def query_sql(self, params: Dict) -> Dict:
        """Query SQL database"""
        # In production: execute actual SQL queries with proper sanitization
        return {
            "rows": [
                {"id": 1, "name": "Q3 Sales", "value": 1234567, "status": "active"},
                {"id": 2, "name": "Q2 Sales", "value": 987654, "status": "complete"}
            ],
            "count": 2,
            "source": "sql_database"
        }
    
    async def create_document(self, params: Dict) -> Dict:
        """Create new document"""
        doc_id = f"doc_{int(datetime.now().timestamp())}"
        return {
            "status": "created",
            "id": doc_id,
            "message": "Document created successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_data(self, params: Dict) -> Dict:
        """Analyze data"""
        return {
            "insights": [
                "Revenue increased by 15% compared to last quarter",
                "Customer acquisition cost decreased by 8%",
                "Top performing region: North America",
                "Employee satisfaction scores improved by 12%"
            ],
            "summary": "Overall positive trends across key metrics",
            "confidence": "high"
        }
    
    async def get_recommendations(self, params: Dict) -> Dict:
        """Get AI recommendations"""
        return {
            "recommendations": [
                "Consider increasing marketing budget in high-performing regions",
                "Focus on customer retention strategies for Q4",
                "Explore automation opportunities to reduce operational costs",
                "Invest in employee training and development programs"
            ],
            "priority": "high",
            "confidence": "high"
        }