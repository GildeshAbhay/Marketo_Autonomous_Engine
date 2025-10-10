"""
Autonomous Report Generator using Gemini API directly.
Combines Marketo data with web research to create comprehensive reports.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from google import genai
from google.genai import types


class AutonomousReportGenerator:
    """Generate comprehensive reports combining Marketo data and web research."""
    
    def __init__(self):
        """Initialize the report generator with Gemini API."""
        # API key should be in environment
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")
        
        self.client = genai.Client(api_key=api_key)
    
    async def generate_comprehensive_report(
        self,
        start_date: str,
        end_date: str,
        marketo_data: Dict[str, Any],
        web_research: List[Dict[str, Any]],
        report_type: str = "comprehensive"
    ) -> str:
        """
        Generate a comprehensive report combining Marketo data and web research.
        
        Args:
            start_date: Start date for report period (YYYY-MM-DD)
            end_date: End date for report period (YYYY-MM-DD)
            marketo_data: Data fetched from Marketo
            web_research: Web search results related to the topic
            report_type: Type of report to generate
            
        Returns:
            Formatted report as markdown string
        """
        
        # Construct the analysis prompt
        prompt = self._build_report_prompt(
            start_date, end_date, marketo_data, web_research, report_type
        )
        
        # Use Gemini to generate comprehensive analysis
        response = self.client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temperature for more factual output
                max_output_tokens=8192,
            )
        )
        
        return response.text
    
    def _build_report_prompt(
        self,
        start_date: str,
        end_date: str,
        marketo_data: Dict[str, Any],
        web_research: List[Dict[str, Any]],
        report_type: str
    ) -> str:
        """Build the prompt for report generation."""
        
        return f"""You are a marketing analytics expert. Generate a comprehensive marketing report based on the following data:

**Report Period:** {start_date} to {end_date}

**Marketo Campaign Data:**
```json
{json.dumps(marketo_data, indent=2)}
```

**Related Industry Research & Insights:**
```json
{json.dumps(web_research, indent=2)}
```

**Instructions:**
Generate a professional marketing report with the following sections:

1. **Executive Summary**
   - Key findings and highlights
   - Performance overview for the period

2. **Campaign Performance Analysis**
   - Detailed breakdown of campaigns from Marketo data
   - Identify top performing campaigns
   - Areas of concern or improvement

3. **Industry Context & Benchmarking**
   - Use the web research data to provide industry context
   - Compare performance against industry standards
   - Relevant trends affecting performance

4. **Key Metrics & KPIs**
   - Engagement rates
   - Conversion metrics
   - ROI indicators

5. **Insights & Recommendations**
   - Actionable insights based on the data
   - Strategic recommendations for improvement
   - Best practices from industry research

6. **Conclusion**
   - Summary of key takeaways
   - Next steps

Format the report in clean markdown with proper headings, bullet points, and tables where appropriate.
Be data-driven and specific. Cite numbers from the Marketo data.
"""


class ReportDataCollector:
    """Collect data from various sources for report generation."""
    
    def __init__(self, host_agent, websearch_agent_url: str = None):
        """Initialize with access to agents."""
        self.host_agent = host_agent
        self.websearch_agent_url = websearch_agent_url
    
    async def collect_marketo_data(
        self,
        start_date: str,
        end_date: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Collect Marketo data for the specified date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            session_id: Session ID for tracking
            
        Returns:
            Dictionary containing Marketo data
        """
        query = f"""
        Get me comprehensive Marketo campaign data from {start_date} to {end_date}.
        Include:
        - All campaigns that were active during this period
        - Campaign performance metrics (opens, clicks, conversions)
        - Lead generation numbers
        - Smart list data if available
        - Any notable trends or patterns
        
        Please provide detailed information.
        """
        
        # Call host agent to get Marketo data
        full_response = ""
        async for event in self.host_agent.stream(
            query=query,
            session_id=session_id
        ):
            if event.get("is_task_complete"):
                full_response = event.get("content", "")
        
        # Parse response into structured format
        return {
            "raw_response": full_response,
            "period": {"start": start_date, "end": end_date},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def collect_web_research(
        self,
        topic: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Collect relevant web research using the web search agent.
        
        Args:
            topic: Research topic
            session_id: Session ID for tracking
            
        Returns:
            List of research results
        """
        queries = [
            f"{topic} marketing trends 2024",
            f"{topic} campaign performance benchmarks",
            f"{topic} best practices marketing automation"
        ]
        
        research_results = []
        
        for query in queries:
            search_query = f"Search for: {query}"
            
            full_response = ""
            async for event in self.host_agent.stream(
                query=search_query,
                session_id=f"{session_id}_research"
            ):
                if event.get("is_task_complete"):
                    full_response = event.get("content", "")
            
            research_results.append({
                "query": query,
                "results": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return research_results