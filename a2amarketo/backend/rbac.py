"""
Role-Based Access Control (RBAC) utilities for Marketo A2A Backend.
This module provides query intent classification and role validation.
"""

import re
from typing import Literal
from fastapi import HTTPException, status

# ============================================================================
# ROLE DEFINITIONS
# ============================================================================

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"

VALID_ROLES = [ROLE_ADMIN, ROLE_ANALYST]


# ============================================================================
# QUERY INTENT CLASSIFICATION
# ============================================================================

def classify_query_intent(query: str) -> Literal["read", "write"]:
    """
    Classify if a query is READ or WRITE based on intent patterns.
    
    Uses context-aware regex patterns to detect write operations.
    
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
    query_lower = query.lower()
    
    # WRITE patterns - specific action phrases with context
    write_patterns = [
        # Campaign triggers
        r'\b(trigger|execute|run|activate|launch|start|fire)\s+(the\s+)?(campaign|smart\s*campaign)',
        r'\btrigger\s+campaign\s*\d+',
        r'\bexecute\s+campaign',
        r'\brun\s+(the\s+)?campaign',
        
        # Campaign/Smart List updates
        r'\b(update|modify|change|edit|alter|rename)\s+(the\s+)?(campaign|smart\s*campaign|smart\s*list)\s+(name|description|settings?|properties?)',
        r'\bupdate\s+(campaign|smart\s*campaign|smart\s*list)\s*\d+',
        r'\bmodify\s+(campaign|smart\s*list)',
        r'\bedit\s+(the\s+)?(campaign|smart\s*list)',
        r'\brename\s+(campaign|smart\s*list)',
        
        # Create operations
        r'\b(create|add|new|make)\s+(a\s+|an\s+)?(campaign|smart\s*campaign|smart\s*list|lead|program)',
        r'\bcreate\s+new',
        
        # Delete operations
        r'\b(delete|remove|drop)\s+(the\s+)?(campaign|smart\s*campaign|smart\s*list|lead)',
        
        # Email/Communication actions
        r'\b(send|schedule|dispatch)\s+(an?\s+)?(email|message|campaign)',
        r'\bschedule\s+(a\s+)?(campaign|email)',
        
        # Lead modifications
        r'\b(update|modify|change)\s+(lead|leads|contact)',
        r'\badd\s+leads?\s+to',
        r'\bremove\s+leads?\s+from',
        
        # Status changes
        r'\b(activate|deactivate|enable|disable)\s+(campaign|program)',
        r'\b(approve|unapprove)\s+(email|landing\s*page|asset)',
    ]
    
    for pattern in write_patterns:
        if re.search(pattern, query_lower):
            return "write"
    
    # Default to read for all other queries
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