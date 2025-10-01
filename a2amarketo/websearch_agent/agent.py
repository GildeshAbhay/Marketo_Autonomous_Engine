import random
from typing import Dict, List, Any
import json

from google.adk.agents import LlmAgent
from google.adk.tools import google_search

# def generate_web_data() -> Dict[str, Any]:
#     """Generates sample web search data for demonstration."""
#     return {
#         "search_results": [
#             {
#                 "title": "Marketo Best Practices Guide",
#                 "url": "https://example.com/marketo-best-practices",
#                 "snippet": "Learn the latest Marketo best practices for lead management and campaign optimization.",
#                 "relevance_score": 95
#             },
#             {
#                 "title": "Marketing Automation Trends 2024",
#                 "url": "https://example.com/marketing-trends-2024",
#                 "snippet": "Discover the top marketing automation trends shaping the industry in 2024.",
#                 "relevance_score": 88
#             },
#             {
#                 "title": "Lead Scoring Strategies",
#                 "url": "https://example.com/lead-scoring-strategies",
#                 "snippet": "Effective lead scoring strategies to improve your marketing ROI.",
#                 "relevance_score": 92
#             }
#         ],
#         "competitor_analysis": [
#             {
#                 "company": "HubSpot",
#                 "strength": "User-friendly interface",
#                 "weakness": "Limited advanced automation"
#             },
#             {
#                 "company": "Pardot",
#                 "strength": "Salesforce integration",
#                 "weakness": "Complex setup process"
#             }
#         ]
#     }


# WEB_DATA = generate_web_data()


# def search_marketo_resources(query: str) -> str:
#     """
#     Searches for Marketo-related resources and information.
    
#     Args:
#         query: Search query string.
    
#     Returns:
#         A string containing search results.
#     """
#     results = WEB_DATA["search_results"]
    
#     # Filter results based on query relevance (simplified)
#     relevant_results = [r for r in results if any(word.lower() in r["title"].lower() or word.lower() in r["snippet"].lower() 
#                                                 for word in query.split())]
    
#     if not relevant_results:
#         relevant_results = results[:2]  # Return top 2 if no specific matches
    
#     result = f"Web Search Results for '{query}':\n\n"
#     for i, result_item in enumerate(relevant_results, 1):
#         result += f"{i}. {result_item['title']}\n"
#         result += f"   URL: {result_item['url']}\n"
#         result += f"   {result_item['snippet']}\n"
#         result += f"   Relevance: {result_item['relevance_score']}%\n\n"
    
#     return result


# def get_marketo_competitors() -> str:
#     """
#     Provides information about Marketo competitors and alternatives.
    
#     Returns:
#         A string containing competitor analysis.
#     """
#     competitors = WEB_DATA["competitor_analysis"]
    
#     result = "Marketo Competitors and Alternatives:\n\n"
#     for competitor in competitors:
#         result += f"• {competitor['company']}\n"
#         result += f"  Strength: {competitor['strength']}\n"
#         result += f"  Weakness: {competitor['weakness']}\n\n"
    
#     return result


# def get_marketo_tutorials() -> str:
#     """
#     Provides links to Marketo tutorials and learning resources.
    
#     Returns:
#         A string containing tutorial information.
#     """
#     tutorials = [
#         {
#             "title": "Marketo University",
#             "url": "https://university.marketo.com",
#             "description": "Official Marketo training and certification programs"
#         },
#         {
#             "title": "Marketo Community",
#             "url": "https://nation.marketo.com",
#             "description": "Community forums and user discussions"
#         },
#         {
#             "title": "Marketo Developer Documentation",
#             "url": "https://developers.marketo.com",
#             "description": "Technical documentation and API guides"
#         }
#     ]
    
#     result = "Marketo Learning Resources:\n\n"
#     for tutorial in tutorials:
#         result += f"• {tutorial['title']}\n"
#         result += f"  URL: {tutorial['url']}\n"
#         result += f"  {tutorial['description']}\n\n"
    
#     return result


# def analyze_marketing_trends() -> str:
#     """
#     Provides analysis of current marketing automation trends.
    
#     Returns:
#         A string containing trend analysis.
#     """
#     trends = [
#         "AI-powered personalization is becoming standard in marketing automation",
#         "Account-based marketing (ABM) integration is growing rapidly",
#         "Multi-channel attribution is improving campaign measurement",
#         "Voice search optimization is emerging as a new focus area",
#         "Privacy-first marketing approaches are gaining importance"
#     ]
    
#     result = "Current Marketing Automation Trends:\n\n"
#     for i, trend in enumerate(trends, 1):
#         result += f"{i}. {trend}\n"
    
#     return result


def create_agent() -> LlmAgent:
    """Constructs the ADK agent for web search and research."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Web_Search_Agent",
        instruction="""
            **Role:** You are a web search and research assistant specializing in research on tasks related to companies , their firmographics and their marketing spend and marketing spend of competitors. 
            Your primary responsibility is to help users find relevant information.
            
        """,
        tools=[google_search,
        ],
    )