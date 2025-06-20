#!/usr/bin/env python3
"""
TIC Industry Research Workflow
Specialized for Testing, Inspection, and Certification (Import/Export)
"""

import asyncio
import aiohttp
import json
import time
import re
from datetime import datetime
from openai import OpenAI
from config import TOOLS, API_CONFIG
from utils import load_environment, check_environment, print_separator
from api_services import get_perplexity_service
from prompts import (
    ROUTER_SYSTEM_PROMPT,
    QUERY_GENERATION_PROMPT,
    QUERY_MAPPING_PROMPT,
    PERPLEXITY_LIST_GENERAL_PROMPT,
    PERPLEXITY_LIST_DOMAIN_PROMPT,
    PERPLEXITY_TIC_GENERAL_PROMPT,
    PERPLEXITY_TIC_DOMAIN_PROMPT
)

class TICResearchWorkflow:
    """TIC industry-specific research workflow for testing, inspection, and certification"""
    
    def __init__(self):
        """Initialize the TIC research workflow"""
        load_environment()
        if not check_environment():
            exit(1)
        
        self.client = OpenAI()
        self.tools = TOOLS
        self.perplexity_service = get_perplexity_service()
    
    async def async_perplexity_search(self, query, domains=None, prompt=None):
        """Async Perplexity search using aiohttp with optional domain filtering and custom prompt"""
        headers = {
            "Authorization": f"Bearer {self.perplexity_service.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use provided prompt or default to list general prompt
        system_prompt = prompt or PERPLEXITY_LIST_GENERAL_PROMPT
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        body = {
            "model": self.perplexity_service.model,
            "messages": messages,
            "temperature": self.perplexity_service.temperature
        }
        
        # Add domain filter if domains are provided
        if domains:
            body["search_domain_filter"] = domains
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.perplexity_service.url, headers=headers, json=body) as response:
                data = await response.json()
                
                # Extract content and citations from response
                content = data['choices'][0]['message']['content']
                citations = data.get('citations', [])  # Perplexity may include citations
                
                return {
                    "content": content,
                    "citations": citations,
                    "raw_response": data  # Keep full response for debugging
                }

    def extract_links_from_content(self, content):
        """Extract URLs from content using regex"""
        url_pattern = r'https?://[^\s\]\)\,\;\"\'\<\>]+'
        links = re.findall(url_pattern, content)
        return list(set(links))  # Remove duplicates
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            # Simple fallback if urllib is not available
            if "://" in url:
                return url.split("://")[1].split("/")[0]
            return url.split("/")[0]
        
    async def generate_tic_specific_queries(self, research_question):
        """Generate TIC industry-specific search queries"""
        print_separator("Generating TIC-Specific Search Queries")
        
        # Use imported prompt
        prompt = QUERY_GENERATION_PROMPT.format(research_question=research_question)
        
        response = self.client.chat.completions.create(
            model=API_CONFIG["openai"]["model"],
            messages=[{"role": "user", "content": prompt}],
            tools=[tool for tool in self.tools if tool["function"]["name"] == "Provide_a_List"],
            tool_choice={"type": "function", "function": {"name": "Provide_a_List"}}
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        queries = args["queries"]
        
        print(f"✅ Generated {len(queries)} TIC-focused search queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        return queries

    async def route_research_request(self, research_question, target_domains=None):
        """Router to decide which research approach to use based on LLM decision"""
        print_separator("🔀 RESEARCH ROUTER")
        
        # Use imported system prompt
        system_prompt = ROUTER_SYSTEM_PROMPT
        
        user_prompt = f"""
        Research Question: {research_question}
        Target Domains: {target_domains if target_domains else 'All TIC websites'}
        
        Decide which research approach to use.
        """
        
        try:
            # Add timeout for router decision (15 seconds)
            router_start = time.time()
            
            # Create the OpenAI call with timeout
            async def make_openai_call():
                return self.client.chat.completions.create(
                    model=API_CONFIG["openai"]["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    tools=self.tools,
                    tool_choice="auto"
                )
            
            # Execute with 15-second timeout
            response = await asyncio.wait_for(make_openai_call(), timeout=15.0)
            
            router_time = time.time() - router_start
            
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                print(f"🤖 Router decided to use: {function_name} (took {router_time:.2f}s)")
                
                if function_name == "Provide_a_List":
                    return await self.execute_provide_list_workflow(research_question, args["queries"])
                elif function_name == "Search_the_Internet":
                    return await self.execute_tic_specific_questions_workflow(args["user_question"], args["target_domains"])
                else:
                    print(f"❌ Unknown tool selected: {function_name}. Stopping.")
                    return None
            else:
                print("❌ No tool selected. Stopping.")
                return None
                
        except asyncio.TimeoutError:
            print("❌ Router timeout: Took longer than 15 seconds to decide. Stopping.")
            return None
        except Exception as e:
            print(f"❌ Error in router: {e}")
            print("🛑 Stopping due to router error.")
            return None

    async def Map_Queries_to_Websites(self, generated_queries):
        """Map generated queries to relevant TIC websites using OpenAI"""
        print_separator("🗺️  MAPPING QUERIES TO WEBSITES")
        
        from tic_industry_websites import TIC_INDUSTRY_WEBSITES
        
        # Get all website domains
        all_websites = [site["domain"] for site in TIC_INDUSTRY_WEBSITES]
        
        # Create mapping prompt using imported prompt
        mapping_prompt = QUERY_MAPPING_PROMPT.format(
            available_websites="\n".join([f"- {site['domain']} ({site['name']})" for site in TIC_INDUSTRY_WEBSITES]),
            queries="\n".join([f"{i+1}. {query}" for i, query in enumerate(generated_queries)])
        )
        
        try:
            response = self.client.chat.completions.create(
                model=API_CONFIG["openai"]["model"],
                messages=[{"role": "user", "content": mapping_prompt}],
                temperature=0.1
            )
            
            # Parse the response to extract JSON
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON array in the response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    mappings = json.loads(json_str)
                else:
                    raise ValueError("No JSON array found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing mapping response: {e}")
                print(f"Response: {response_text}")
                # Fallback: map all queries to all websites
                mappings = [
                    {"query": query, "websites": all_websites}
                    for query in generated_queries
                ]
            
            print(f"✅ Mapped {len(mappings)} queries to websites:")
            for mapping in mappings:
                print(f"  Query: {mapping['query'][:50]}...")
                print(f"  Websites: {len(mapping['websites'])} sites")
            
            return mappings
            
        except Exception as e:
            print(f"❌ Error in query mapping: {e}")
            # Fallback: map all queries to all websites
            mappings = [
                {"query": query, "websites": all_websites}
                for query in generated_queries
            ]
            return mappings

    async def execute_provide_list_workflow(self, research_question, queries):
        """Execute Provide_a_List workflow - comprehensive research approach"""
        print_separator("📋 EXECUTING PROVIDE LIST WORKFLOW")
        workflow_start = time.time()
        
        # Phase 1: Map queries to relevant websites
        query_mappings = await self.Map_Queries_to_Websites(queries)
        
        # Phase 2: Prepare search tasks
        search_tasks = []
        
        # Add general web searches for all queries
        for query in queries:
            search_tasks.append({
                "type": "general_web",
                "query": query,
                "websites": []
            })
        
        # Add domain-filtered searches for mapped queries
        for mapping in query_mappings:
            if mapping["websites"]:
                search_tasks.append({
                    "type": "domain_filtered",
                    "query": mapping["query"],
                    "websites": mapping["websites"]  # All mapped websites for this query
                })
        
        # Phase 3: Execute all searches in parallel
        print_separator("Executing Parallel Searches")
        
        async def execute_search_task(task):
            if task["type"] == "general_web":
                return await self.async_perplexity_search(task["query"], prompt=PERPLEXITY_LIST_GENERAL_PROMPT)
            else:  # domain_filtered
                return await self.async_perplexity_search(task["query"], domains=task["websites"], prompt=PERPLEXITY_LIST_DOMAIN_PROMPT)
        
        # Execute all searches in parallel
        search_results = await asyncio.gather(*[execute_search_task(task) for task in search_tasks], return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(search_results):
            task = search_tasks[i]
            if isinstance(result, dict):
                processed_results.append({
                    "query": task["query"],
                    "result": result["content"],
                    "citations": result["citations"],
                    "extracted_links": self.extract_links_from_content(result["content"]),
                    "status": "success",
                    "search_type": task["type"],
                    "websites": task["websites"]
                })
            else:
                processed_results.append({
                    "query": task["query"],
                    "result": f"Error: {str(result)}",
                    "citations": [],
                    "extracted_links": [],
                    "status": "error",
                    "search_type": task["type"],
                    "websites": task["websites"]
                })
        
        # Compile results
        result_data = {
            "research_question": research_question,
            "industry_focus": "TIC (Testing, Inspection, Certification)",
            "workflow_type": "provide_list_workflow",
            "query_mappings": query_mappings,
            "execution_summary": {
                "total_time_seconds": time.time() - workflow_start,
                "workflow_type": "provide_list_workflow",
                "total_searches": len(search_tasks),
                "general_searches": len([t for t in search_tasks if t["type"] == "general_web"]),
                "domain_searches": len([t for t in search_tasks if t["type"] == "domain_filtered"])
            },
            "search_results": processed_results,
            "timestamp": datetime.now().isoformat()
        }
        
        filename = self.save_tic_results(result_data)
        
        print_separator("📋 PROVIDE LIST WORKFLOW COMPLETE")
        print(f"⏱️  Total Time: {time.time() - workflow_start:.2f} seconds")
        print(f"📊 Total Searches: {len(search_tasks)}")
        print(f"🌐 General Web Searches: {len([t for t in search_tasks if t['type'] == 'general_web'])}")
        print(f"🏢 Domain-Filtered Searches: {len([t for t in search_tasks if t['type'] == 'domain_filtered'])}")
        print(f"💾 Results saved to: {filename}")
        
        return result_data

    async def execute_tic_specific_questions_workflow(self, user_question, target_domains):
        """Execute TIC Specific Questions workflow - direct search approach with intelligent mapping"""
        print_separator("🎯 EXECUTING TIC SPECIFIC QUESTIONS WORKFLOW")
        workflow_start = time.time()
        
        # Phase 1: Map single user question to relevant websites
        query_mappings = await self.Map_Queries_to_Websites([user_question])
        
        # Phase 2: Prepare search tasks
        search_tasks = []
        
        # Add general web search for the question
        search_tasks.append({
            "type": "general_web",
            "query": user_question,
            "websites": []
        })
        
        # Add domain-filtered search for mapped query
        if query_mappings and query_mappings[0]["websites"]:
            search_tasks.append({
                "type": "domain_filtered",
                "query": user_question,
                "websites": query_mappings[0]["websites"]  # All mapped websites for this query
            })
        
        # Phase 3: Execute all searches in parallel
        print_separator("Executing Direct Searches")
        
        async def execute_search_task(task):
            if task["type"] == "general_web":
                return await self.async_perplexity_search(task["query"], prompt=PERPLEXITY_TIC_GENERAL_PROMPT)
            else:  # domain_filtered
                return await self.async_perplexity_search(task["query"], domains=task["websites"], prompt=PERPLEXITY_TIC_DOMAIN_PROMPT)
        
        # Execute all searches in parallel
        search_results = await asyncio.gather(*[execute_search_task(task) for task in search_tasks], return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(search_results):
            task = search_tasks[i]
            if isinstance(result, dict):
                processed_results.append({
                    "query": task["query"],
                    "result": result["content"],
                    "citations": result["citations"],
                    "extracted_links": self.extract_links_from_content(result["content"]),
                    "status": "success",
                    "search_type": task["type"],
                    "websites": task["websites"]
                })
            else:
                processed_results.append({
                    "query": task["query"],
                    "result": f"Error: {str(result)}",
                    "citations": [],
                    "extracted_links": [],
                    "status": "error",
                    "search_type": task["type"],
                    "websites": task["websites"]
                })
        
        # Compile results
        result_data = {
            "research_question": user_question,
            "industry_focus": "TIC (Testing, Inspection, Certification)",
            "workflow_type": "tic_specific_questions",
            "target_domains": target_domains,
            "query_mappings": query_mappings,
            "execution_summary": {
                "total_time_seconds": time.time() - workflow_start,
                "workflow_type": "tic_specific_questions",
                "total_searches": len(search_tasks),
                "general_searches": len([t for t in search_tasks if t["type"] == "general_web"]),
                "domain_searches": len([t for t in search_tasks if t["type"] == "domain_filtered"])
            },
            "search_results": processed_results,
            "timestamp": datetime.now().isoformat()
        }
        
        filename = self.save_tic_results(result_data)
        
        print_separator("🎯 TIC SPECIFIC QUESTIONS WORKFLOW COMPLETE")
        print(f"⏱️  Total Time: {time.time() - workflow_start:.2f} seconds")
        print(f"📊 Total Searches: {len(search_tasks)}")
        print(f"🌐 General Web Searches: {len([t for t in search_tasks if t['type'] == 'general_web'])}")
        print(f"🏢 Domain-Filtered Searches: {len([t for t in search_tasks if t['type'] == 'domain_filtered'])}")
        print(f"💾 Results saved to: {filename}")
        
        return result_data

    def save_tic_results(self, result_data):
        """Save TIC research results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_question = "".join(c for c in result_data["research_question"][:50] if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"research_results/tic_research_{safe_question}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            return filename
        except Exception as e:
            print(f"Error saving TIC research results: {e}")
            return None

async def main():
    """Main function for TIC industry research"""
    print_separator("🔬 TIC INDUSTRY RESEARCH SYSTEM")
    print("Specialized for Testing, Inspection, Certification (Import/Export)")
    
    # Get research question
    research_question = input("\n📝 Enter your TIC research question: ").strip()
    if not research_question:
        print("❌ No research question provided")
        return
    
    # Get target domains (optional)
    target_domains_input = input("\n🎯 Enter target domains (comma-separated, or press Enter for all TIC websites): ").strip()
    target_domains = None
    
    if target_domains_input:
        target_domains = [domain.strip() for domain in target_domains_input.split(",") if domain.strip()]
        print(f"✅ Using specified domains: {target_domains}")
    else:
        print("✅ Using all TIC websites for comprehensive research")
    
    # Run TIC research with router
    workflow = TICResearchWorkflow()
    result = await workflow.route_research_request(research_question, target_domains)
    
    # Handle router failure cases
    if result is None:
        print_separator("🛑 RESEARCH STOPPED")
        print("❌ Unable to process your request due to:")
        print("   • Router timeout (>15 seconds)")
        print("   • No tool selected")
        print("   • Unknown tool selected")
        print("   • Router error")
        print("\n💡 Try rephrasing your question or try again later.")
        return
    
    print_separator("✅ RESEARCH COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(main()) 