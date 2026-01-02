"""
Command Service for Medical AI Platform
Handles slash command parsing and execution

Supports commands:
- /flashcard <topic> - Generate flashcards
- /mcq <topic> - Generate multiple choice questions
- /highyield <topic> - Generate high-yield summary points
- /explain <topic> - Provide detailed explanations
- /map <topic> - Generate concept maps

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7
"""
import re
from typing import Dict, Optional, Any
from supabase import Client
from services.text_formatter import clean_markdown


class CommandService:
    """Service for parsing and executing slash commands"""
    
    # Supported commands
    SUPPORTED_COMMANDS = {
        'flashcard': 'generate_flashcards',
        'mcq': 'generate_mcqs',
        'highyield': 'generate_summary',
        'explain': 'generate_explanation',
        'map': 'generate_concept_map'
    }
    
    def __init__(self, supabase_client: Client):
        """
        Initialize command service
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
    
    def parse_command(self, message: str) -> Optional[Dict[str, str]]:
        """
        Parse a message to detect and extract slash commands
        
        Args:
            message: User message that may contain a slash command
            
        Returns:
            Dict with 'command' and 'topic' keys if command found, None otherwise
            
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        # Check if message starts with a slash
        if not message.strip().startswith('/'):
            return None
        
        # Pattern: /command topic
        # Matches: /flashcard diabetes, /mcq cardiology, etc.
        pattern = r'^/(\w+)\s+(.+)$'
        match = re.match(pattern, message.strip())
        
        if not match:
            return None
        
        command = match.group(1).lower()
        topic = match.group(2).strip()
        
        # Validate command is supported
        if command not in self.SUPPORTED_COMMANDS:
            return None
        
        return {
            'command': command,
            'topic': topic
        }
    
    async def execute_command(
        self,
        user_id: str,
        command: str,
        topic: str
    ) -> Dict[str, Any]:
        """
        Execute a slash command
        
        Args:
            user_id: User's unique identifier
            command: Command name (flashcard, mcq, etc.)
            topic: Topic for the command
            
        Returns:
            Dict containing the command result
            
        Raises:
            Exception: If command execution fails
            
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        if command not in self.SUPPORTED_COMMANDS:
            raise Exception(f"Unsupported command: {command}")
        
        # Get the handler method name
        handler_name = self.SUPPORTED_COMMANDS[command]
        handler = getattr(self, handler_name)
        
        # Execute the handler
        result = await handler(user_id, topic)
        
        return result
    
    async def generate_flashcards(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate flashcards for a given topic
        
        Args:
            user_id: User's unique identifier
            topic: Topic for flashcard generation
            
        Returns:
            Dict containing generated flashcards
            
        Requirements: 4.1, 4.7
        """
        from services.model_router import get_model_router_service
        from services.rate_limiter import get_rate_limiter
        
        router = get_model_router_service(self.supabase)
        
        # Create prompt for flashcard generation
        prompt = f"""Generate 5-7 medical flashcards about {topic}.

Format each flashcard as:
Q: [Question]
A: [Answer]

Focus on key concepts, definitions, and clinical relevance."""
        
        # Select provider and execute
        provider = await router.select_provider("flashcard")
        result = await router.execute_with_fallback(
            provider=provider,
            feature="flashcard",
            prompt=prompt,
            system_prompt="You are a medical education expert creating flashcards for medical students."
        )
        
        if not result["success"]:
            raise Exception(f"Failed to generate flashcards: {result.get('error', 'Unknown error')}")
        
        # Clean markdown formatting from content
        cleaned_content = clean_markdown(result["content"])
        
        # Track usage (Requirement 4.7)
        rate_limiter = get_rate_limiter(self.supabase)
        await rate_limiter.increment_usage(
            user_id=user_id,
            tokens=result["tokens_used"],
            feature="flashcard"
        )
        
        return {
            "command": "flashcard",
            "topic": topic,
            "content": cleaned_content,
            "tokens_used": result["tokens_used"]
        }
    
    async def generate_mcqs(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate multiple choice questions for a given topic
        
        Args:
            user_id: User's unique identifier
            topic: Topic for MCQ generation
            
        Returns:
            Dict containing generated MCQs
            
        Requirements: 4.2, 4.7
        """
        from services.model_router import get_model_router_service
        from services.rate_limiter import get_rate_limiter
        
        router = get_model_router_service(self.supabase)
        
        # Create prompt for MCQ generation
        prompt = f"""Generate 5 multiple choice questions about {topic}.

Format each question as:
Q[number]: [Question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct Answer: [Letter]
Explanation: [Brief explanation]

Focus on clinically relevant scenarios and USMLE-style questions."""
        
        # Select provider and execute
        provider = await router.select_provider("mcq")
        result = await router.execute_with_fallback(
            provider=provider,
            feature="mcq",
            prompt=prompt,
            system_prompt="You are a medical education expert creating USMLE-style multiple choice questions."
        )
        
        if not result["success"]:
            raise Exception(f"Failed to generate MCQs: {result.get('error', 'Unknown error')}")
        
        # Clean markdown formatting from content
        cleaned_content = clean_markdown(result["content"])
        
        # Track usage (Requirement 4.7)
        rate_limiter = get_rate_limiter(self.supabase)
        await rate_limiter.increment_usage(
            user_id=user_id,
            tokens=result["tokens_used"],
            feature="mcq"
        )
        
        return {
            "command": "mcq",
            "topic": topic,
            "content": cleaned_content,
            "tokens_used": result["tokens_used"]
        }
    
    async def generate_summary(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate high-yield summary points for a given topic
        
        Args:
            user_id: User's unique identifier
            topic: Topic for summary generation
            
        Returns:
            Dict containing generated summary
            
        Requirements: 4.3
        """
        from services.model_router import get_model_router_service
        
        router = get_model_router_service(self.supabase)
        
        # Create prompt for summary generation
        prompt = f"""Generate high-yield summary points about {topic}.

Format:
# {topic} - High-Yield Points

- [Key point 1]
- [Key point 2]
- [Key point 3]
...

Focus on the most important, testable information for medical students."""
        
        # Select provider and execute
        provider = await router.select_provider("highyield")
        result = await router.execute_with_fallback(
            provider=provider,
            feature="highyield",
            prompt=prompt,
            system_prompt="You are a medical education expert creating concise, high-yield summaries."
        )
        
        if not result["success"]:
            raise Exception(f"Failed to generate summary: {result.get('error', 'Unknown error')}")
        
        # Clean markdown formatting from content
        cleaned_content = clean_markdown(result["content"])
        
        return {
            "command": "highyield",
            "topic": topic,
            "content": cleaned_content,
            "tokens_used": result["tokens_used"]
        }
    
    async def generate_explanation(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate detailed explanation for a given topic
        
        Args:
            user_id: User's unique identifier
            topic: Topic for explanation
            
        Returns:
            Dict containing generated explanation
            
        Requirements: 4.4
        """
        from services.model_router import get_model_router_service
        
        router = get_model_router_service(self.supabase)
        
        # Create prompt for explanation generation
        prompt = f"""Provide a detailed, clear explanation of {topic}.

Include:
1. Definition and overview
2. Key mechanisms or pathophysiology
3. Clinical significance
4. Important details for medical students

Use clear language and organize the information logically."""
        
        # Select provider and execute
        provider = await router.select_provider("explain")
        result = await router.execute_with_fallback(
            provider=provider,
            feature="explain",
            prompt=prompt,
            system_prompt="You are a medical education expert providing clear, detailed explanations."
        )
        
        if not result["success"]:
            raise Exception(f"Failed to generate explanation: {result.get('error', 'Unknown error')}")
        
        # Clean markdown formatting from content
        cleaned_content = clean_markdown(result["content"])
        
        return {
            "command": "explain",
            "topic": topic,
            "content": cleaned_content,
            "tokens_used": result["tokens_used"]
        }
    
    async def generate_concept_map(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate concept map for a given topic
        
        Args:
            user_id: User's unique identifier
            topic: Topic for concept map
            
        Returns:
            Dict containing generated concept map
            
        Requirements: 4.5
        """
        from services.model_router import get_model_router_service
        
        router = get_model_router_service(self.supabase)
        
        # Create prompt for concept map generation
        prompt = f"""Create a concept map for {topic}.

Format as a text-based hierarchical structure:

{topic}
├── Main Concept 1
│   ├── Sub-concept 1.1
│   └── Sub-concept 1.2
├── Main Concept 2
│   ├── Sub-concept 2.1
│   └── Sub-concept 2.2
└── Main Concept 3

Show relationships and hierarchies between key concepts."""
        
        # Select provider and execute
        provider = await router.select_provider("map")
        result = await router.execute_with_fallback(
            provider=provider,
            feature="map",
            prompt=prompt,
            system_prompt="You are a medical education expert creating concept maps to show relationships between ideas."
        )
        
        if not result["success"]:
            raise Exception(f"Failed to generate concept map: {result.get('error', 'Unknown error')}")
        
        # Clean markdown formatting from content
        cleaned_content = clean_markdown(result["content"])
        
        return {
            "command": "map",
            "topic": topic,
            "content": cleaned_content,
            "tokens_used": result["tokens_used"]
        }


# Singleton instance
_command_service_instance = None


def get_command_service(supabase_client: Client) -> CommandService:
    """
    Get or create command service singleton instance
    
    Args:
        supabase_client: Supabase client instance
        
    Returns:
        CommandService instance
    """
    global _command_service_instance
    if _command_service_instance is None:
        _command_service_instance = CommandService(supabase_client)
    return _command_service_instance
