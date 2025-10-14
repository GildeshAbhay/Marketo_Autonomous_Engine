"""
Role-Based Access Control (RBAC) utilities for Marketo A2A Backend.
This module provides query intent classification using Gemini API and role validation.
"""

import os
import json
from typing import Literal
from fastapi import HTTPException, status
from google import genai
from google.genai import types

# ============================================================================
# ROLE DEFINITIONS
# ============================================================================

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"

VALID_ROLES = [ROLE_ADMIN, ROLE_ANALYST]


# ============================================================================
# GEMINI CLIENT INITIALIZATION
# ============================================================================

class IntentClassifier:
    """Singleton class to manage Gemini client for intent classification."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IntentClassifier, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable required for intent classification"
            )
        self._client = genai.Client(api_key=api_key)
    
    def classify_intent(self, query: str) -> Literal["read", "write"]:
        """
        Classify query intent using Gemini API with structured JSON output.
        
        Args:
            query: The user's natural language query
            
        Returns:
            "read" or "write"
        """
        prompt = f"""Analyze the following user query and determine if it represents a READ or WRITE operation in a marketing automation system (Marketo).

**Query:** "{query}"

**Classification Guidelines:**

**WRITE operations** include:
- Triggering, executing, running, activating, launching, or firing campaigns
- Creating new campaigns, smart lists, leads, programs, or assets
- Updating, modifying, changing, editing, or renaming existing campaigns, smart lists, or leads
- Deleting or removing campaigns, smart lists, leads, or assets
- Sending, scheduling, or dispatching emails or campaigns
- Adding or removing leads from lists or programs
- Activating, deactivating, enabling, or disabling campaigns or programs
- Approving or unapproving emails, landing pages, or assets

**READ operations** include:
- Getting, fetching, retrieving, viewing, or showing information
- Listing, searching, or filtering data
- Generating reports or analytics
- Describing or explaining assets or configurations
- Checking status or viewing history
- Any query that only retrieves or displays information without modifying data

Return your analysis as a JSON object with the following structure:
{{
  "intent": "read" or "write",
  "confidence": "high" or "medium" or "low",
  "reasoning": "brief explanation of why this was classified as read or write"
}}

**Important:** Only return valid JSON. The "intent" field must be exactly "read" or "write" (lowercase).
"""

        try:
            response = self._client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Very low temperature for consistent classification
                    max_output_tokens=256,
                    response_mime_type="application/json",  # Force JSON output
                )
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            intent = result.get("intent", "").lower()
            
            # Validate the response
            if intent not in ["read", "write"]:
                print(f"⚠️ Invalid intent from Gemini: {intent}. Defaulting to 'read'")
                return "read"
            
            # Log for debugging (optional)
            confidence = result.get("confidence", "unknown")
            reasoning = result.get("reasoning", "No reasoning provided")
            print(f"🤖 Intent Classification: {intent} (confidence: {confidence})")
            print(f"   Reasoning: {reasoning}")
            
            return intent
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Gemini response as JSON: {e}")
            print(f"   Raw response: {response.text if 'response' in locals() else 'No response'}")
            # Fallback to regex-based classification
            return self._fallback_regex_classification(query)
            
        except Exception as e:
            print(f"❌ Error calling Gemini API for intent classification: {e}")
            # Fallback to regex-based classification
            return self._fallback_regex_classification(query)
    
    def _fallback_regex_classification(self, query: str) -> Literal["read", "write"]:
        """
        Fallback regex-based classification if Gemini API fails.
        This is the original regex logic kept as a safety net.
        """
        import re
        
        query_lower = query.lower()
        
        write_patterns = [
            r'\b(trigger|execute|run|activate|launch|start|fire)\s+(the\s+)?(campaign|smart\s*campaign)',
            r'\btrigger\s+campaign\s*\d+',
            r'\bexecute\s+campaign',
            r'\brun\s+(the\s+)?campaign',
            r'\b(update|modify|change|edit|alter|rename)\s+(the\s+)?(campaign|smart\s*campaign|smart\s*list)\s+(name|description|settings?|properties?)',
            r'\bupdate\s+(campaign|smart\s*campaign|smart\s*list)\s*\d+',
            r'\bmodify\s+(campaign|smart\s*list)',
            r'\bedit\s+(the\s+)?(campaign|smart\s*list)',
            r'\brename\s+(campaign|smart\s*list)',
            r'\b(create|add|new|make)\s+(a\s+|an\s+)?(campaign|smart\s*campaign|smart\s*list|lead|program)',
            r'\bcreate\s+new',
            r'\b(delete|remove|drop)\s+(the\s+)?(campaign|smart\s*campaign|smart\s*list|lead)',
            r'\b(send|schedule|dispatch)\s+(an?\s+)?(email|message|campaign)',
            r'\bschedule\s+(a\s+)?(campaign|email)',
            r'\b(update|modify|change)\s+(lead|leads|contact)',
            r'\badd\s+leads?\s+to',
            r'\bremove\s+leads?\s+from',
            r'\b(activate|deactivate|enable|disable)\s+(campaign|program)',
            r'\b(approve|unapprove)\s+(email|landing\s*page|asset)',
        ]
        
        for pattern in write_patterns:
            if re.search(pattern, query_lower):
                return "write"
        
        return "read"


# Global classifier instance
_classifier = None

def get_classifier() -> IntentClassifier:
    """Get or create the global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier


# ============================================================================
# QUERY INTENT CLASSIFICATION
# ============================================================================

def classify_query_intent(query: str) -> Literal["read", "write"]:
    """
    Classify if a query is READ or WRITE using Gemini API.
    
    This function uses Gemini to understand the intent of natural language queries
    with better context awareness than regex patterns.
    
    Args:
        query: The user's natural language query
        
    Returns:
        "read" or "write"
        
    Examples:
        >>> classify_query_intent("Get campaign details for ID 123")
        'read'
        >>> classify_query_intent("Trigger campaign 123 with leads")
        'write'
        >>> classify_query_intent("Show me the update history")
        'read'
        >>> classify_query_intent("Update campaign 456 name to New Name")
        'write'
    """
    try:
        classifier = get_classifier()
        return classifier.classify_intent(query)
    except Exception as e:
        print(f"❌ Critical error in intent classification: {e}")
        # Ultimate fallback: default to read for safety
        return "read"


def validate_user_query_permission(query: str, user_role: str) -> None:
    """
    Validate if a user has permission to execute a query based on their role.
    
    Raises HTTPException if user lacks permission.
    
    Args:
        query: The user's natural language query
        user_role: The user's role (admin, analyst)
        
    Raises:
        HTTPException: 403 if analyst tries to perform write operation
        HTTPException: 400 if invalid role provided
    """
    if user_role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_role}"
        )
    
    # Admins can do anything
    if user_role == ROLE_ADMIN:
        return
    
    # Analysts can only perform read operations
    intent = classify_query_intent(query)
    
    if intent == "write":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Permission denied. Your query appears to request a write operation "
                "(trigger, update, create, delete). Analysts can only perform read operations. "
                "Please contact an administrator if you need to perform this action."
            )
        )


# ============================================================================
# ROLE REQUIREMENT UTILITIES
# ============================================================================

def require_admin_role(user_role: str) -> None:
    """
    Validate that user has admin role.
    
    Args:
        user_role: The user's role
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if user_role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this operation"
        )


def require_analyst_or_admin_role(user_role: str) -> None:
    """
    Validate that user has analyst or admin role.
    
    Args:
        user_role: The user's role
        
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    if user_role not in [ROLE_ADMIN, ROLE_ANALYST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Analyst or Admin role required."
        )


# ============================================================================
# ROLE DISPLAY HELPERS
# ============================================================================

def get_role_permissions_info(role: str) -> dict:
    """
    Get information about what permissions a role has.
    
    Args:
        role: The role name
        
    Returns:
        Dictionary with role permissions info
    """
    permissions = {
        ROLE_ADMIN: {
            "role": "Admin",
            "description": "Full access to all operations",
            "can_read": True,
            "can_write": True,
            "allowed_operations": [
                "View campaigns, smart lists, and leads",
                "Generate reports and analytics",
                "Trigger campaigns",
                "Update campaigns and smart lists",
                "Create new assets",
                "Delete assets",
            ]
        },
        ROLE_ANALYST: {
            "role": "Analyst",
            "description": "Read-only access for analysis and reporting",
            "can_read": True,
            "can_write": False,
            "allowed_operations": [
                "View campaigns, smart lists, and leads",
                "Generate reports and analytics",
                "Search and filter data",
                "View historical data",
            ]
        }
    }
    
    return permissions.get(role, {
        "role": "Unknown",
        "description": "Invalid role",
        "can_read": False,
        "can_write": False,
        "allowed_operations": []
    })