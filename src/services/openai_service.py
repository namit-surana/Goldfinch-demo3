"""
OpenAI service integration
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..config import API_CONFIG, TOOLS
from ..models.responses import ResearchQueries, QueryMappings


class OpenAIService:
    """Service class for OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI()
        self.model = API_CONFIG["openai"]["model"]
        self.tools = TOOLS
    
    async def get_router_decision(self, research_question: str, chat_history: Optional[List[Dict]] = None) -> Optional[Dict[str, str]]:
        """Get router decision for which workflow to use"""
        from ..config import ROUTER_SYSTEM_PROMPT
        
      
        
        full_message = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]
        
        full_message.extend(chat_history or [])
        # print(full_message)
       
        
        try:
            # Add timeout for router decision (15 seconds)
            router_start = time.time()
            
            # Create the OpenAI call with timeout
            async def make_openai_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=full_message,
                    tools=self.tools,
                    tool_choice="auto"
                )
            
            # Execute with 15-second timeout
            response = await asyncio.wait_for(make_openai_call(), timeout=15.0)
            
            # print("[OPENAI SERVICE] router response:", response)
            
            router_time = time.time() - router_start
            
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)["query"]
                print(f"🤖 Router decided to use: {function_name}\nwith query: {function_args}\n(took {router_time:.2f}s)")
                return {"type": function_name, "content": function_args}
            else:
                # No tool selected - return the LLM's direct response
                direct_response = response.choices[0].message.content
                print(f"🤖 No tool selected - returning direct LLM response (took {router_time:.2f}s)")
                return {"type": "direct_response", "content": direct_response}
                
        except asyncio.TimeoutError:
            print("❌ Router timeout: Took longer than 15 seconds to decide. Stopping.")
            return None
        except Exception as e:
            print(f"❌ Error in router: {e}")
            print("🛑 Stopping due to router error.")
            return None
    
    async def generate_research_queries(self, router_decision: str, router_query: str) -> List[str]:
        """Generate multiple research queries for comprehensive analysis"""
        from ..config import LIST_QUERY_GENERATION_PROMPT, SEARCH_INTERNET_QUERY_GENERATION_PROMPT
        
        print("[OPENAI SERVICE] generate_research_queries called with:", router_decision, router_query)
        
        try:
            if router_decision == "Provide_a_List":
                SYSTEM_PROMPT = LIST_QUERY_GENERATION_PROMPT
            elif router_decision == "Search_the_Internet":
                SYSTEM_PROMPT = SEARCH_INTERNET_QUERY_GENERATION_PROMPT
            else:
                return [router_query]
            
            print("[OPENAI SERVICE] SYSTEM_PROMPT:", SYSTEM_PROMPT)
            
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Research Question: {router_query}"}
                ],
                text_format=ResearchQueries
            )
            # print("[OPENAI SERVICE] generate_research_queries response:", response)
            queries = response.output_parsed.queries
            print(f"✅ Generated {len(queries)} research queries:")
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
            return queries
        except Exception as e:
            print(f"❌ Error generating queries: {e}")
            # Fallback: use the original question
            return [router_query]
    
    async def map_queries_to_websites(self, generated_queries: List[str], dynamic_websites: List[Dict]) -> List[Dict[str, Any]]:
        """Map generated queries to relevant websites using OpenAI"""
        from ..config import QUERY_MAPPING_PROMPT
        
        print("[OPENAI SERVICE] map_queries_to_websites called with:", generated_queries, dynamic_websites)
        
        # Create rich website descriptions using all available metadata
        rich_website_descriptions = [
    (
        f"Website: {site['name']}\n"
        f"- Domain: {site.get('domain', 'N/A')}\n"
        f"- Region: {site.get('region', 'N/A')}\n"
        f"- Organization Type: {site.get('org_type', 'N/A')}\n"
        f"- Aliases: {', '.join(site.get('aliases', [])) or 'None'}\n"
        f"- Industry Focus: {', '.join(site.get('industry_tags', [])) or 'General'}\n"
        f"- Semantic Profile: {site.get('semantic_profile', '')}\n"
        f"- Boost Keywords: {', '.join(site.get('boost_keywords', [])) or 'None'}"
    ).strip()
    for site in dynamic_websites
]

        # Use the existing QUERY_MAPPING_PROMPT from prompts.py
        available_websites="\n\n".join(rich_website_descriptions),
        queries="\n".join([f"{i+1}. {query}" for i, query in enumerate(generated_queries)])

        user_prompt = f"Research Queries: {queries}\nWebsites: {available_websites}\n"

        print("[OPENAI SERVICE] user_prompt:", user_prompt)

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": QUERY_MAPPING_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=QueryMappings
            )
            print("[OPENAI SERVICE] map_queries_to_websites response:", response)
            # Debug: Print the raw output_parsed from OpenAI
            print(f"[DEBUG] OpenAI mapping response.output_parsed: {response.output_parsed}")
            mappings = [
                {"query": mapping.query, "websites": mapping.websites}
                for mapping in response.output_parsed.mappings
            ]
            # Fallback: If LLM returns wrong number of mappings, use default mapping
            if len(mappings) != len(generated_queries):
                print(f"[WARNING] LLM returned {len(mappings)} mappings, but expected {len(generated_queries)}. Falling back to default mapping.")
                all_websites = [site["domain"] for site in dynamic_websites]
                mappings = [
                    {"query": query, "websites": all_websites}
                    for query in generated_queries
                ]
            print(f"✅ Mapped {len(mappings)} queries to websites:")
            for mapping in mappings:
                print(f"  Query: {mapping['query'][:10]}...")
                print(f"  Websites: {len(mapping['websites'])} sites")
            return mappings
        except Exception as e:
            print(f"❌ Error in query mapping: {e}")
            # Fallback: map all queries to all websites
            all_websites = [site["domain"] for site in dynamic_websites]
            mappings = [
                {"query": query, "websites": all_websites}
                for query in generated_queries
            ]
            return mappings

    async def generate_research_summary(self, research_results: Dict[str, Any]) -> str:
        """Generate a summary of research results using OpenAI"""
        from ..config import RESEARCH_SUMMARY_SYSTEM_PROMPT
        
        print("[OPENAI SERVICE] generate_research_summary called")
        
        try:
            # Convert research results to a user-friendly format
            user_prompt = f"""
Research Question: {research_results.get('research_question', 'N/A')}
Workflow Type: {research_results.get('workflow_type', 'N/A')}
Execution Summary: {research_results.get('execution_summary', {})}

Search Results:
{json.dumps(research_results.get('search_results', []), indent=2)}

Please provide a comprehensive summary of these research findings.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": RESEARCH_SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            summary = response.choices[0].message.content
            print(f"✅ Generated research summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating research summary: {e}")
            # Fallback: return a basic summary
            return f"Research completed for: {research_results.get('research_question', 'N/A')}. Found {len(research_results.get('search_results', []))} search results." 
