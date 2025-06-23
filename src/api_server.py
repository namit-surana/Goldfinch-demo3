#!/usr/bin/env python3
"""
TIC Research API Server
FastAPI-based API for TIC industry research with dynamic domain configuration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import time
import uuid
from datetime import datetime

# Import our TIC research system
from src.tic_research import TICResearchWorkflow
from src.config import TOOLS, API_CONFIG
from src.utils import print_separator
from src.prompts import (
    ROUTER_SYSTEM_PROMPT,
    LIST_QUERY_GENERATION_PROMPT,
    SEARCH_INTERNET_QUERY_GENERATION_PROMPT,
    QUERY_MAPPING_PROMPT,
    PERPLEXITY_LIST_GENERAL_PROMPT,
    PERPLEXITY_LIST_DOMAIN_PROMPT,
    PERPLEXITY_TIC_GENERAL_PROMPT,
    PERPLEXITY_TIC_DOMAIN_PROMPT
)

# Initialize FastAPI app
app = FastAPI(
    title="TIC Research API",
    description="An API for conducting Testing, Inspection, and Certification (TIC) research.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class DomainMetadata(BaseModel):
    name: str
    homepage: str
    domain: str
    region: str
    org_type: str
    aliases: List[str] = []
    industry_tags: List[str] = []
    semantic_profile: str
    boost_keywords: List[str] = []


class ResearchRequest(BaseModel):
    research_question: str = Field(..., description="The research question to investigate")
    domain_list_metadata: List[DomainMetadata] = Field(..., description="List of domain metadata for TIC websites")
    chat_history: List[Dict[str, str]] = Field(default=[], description="Previous chat messages for context")

class ResearchStartResponse(BaseModel):
    """Response model for when research is successfully queued"""
    request_id: str
    status: str
    message: str
    research_question: str
    timestamp: str

class ResearchResultResponse(BaseModel):
    """Response model for the final research results"""
    request_id: str
    status: str
    message: str
    research_question: str
    workflow_type: Optional[str] = None
    execution_summary: Optional[Dict[str, Any]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    query_mappings: Optional[List[Dict[str, Any]]] = None
    timestamp: str
    processing_time: Optional[float] = None

class StatusResponse(BaseModel):
    request_id: str
    status: str
    message: str
    progress: Optional[float] = None

class DynamicTICResearchWorkflow(TICResearchWorkflow):
    """Extended TIC research workflow that can use dynamic domain metadata"""
    
    def __init__(self, domain_metadata: List[DomainMetadata]):
        super().__init__()
        self.domain_metadata = domain_metadata
        self.dynamic_websites = self._convert_metadata_to_websites()
    
    def _convert_metadata_to_websites(self):
        """Convert domain metadata to the format expected by the mapping function"""
        websites = []
        for domain in self.domain_metadata:
            websites.append({
                "name": domain.name,
                "domain": domain.domain,
                "homepage": domain.homepage,
                "region": domain.region,
                "org_type": domain.org_type,
                "aliases": domain.aliases,
                "industry_tags": domain.industry_tags,
                "semantic_profile": domain.semantic_profile,
                "boost_keywords": domain.boost_keywords
            })
        return websites
    
    def save_tic_results(self, result_data):
        """Override to not save files - just return the data"""
        # Don't save to file, just return the data
        return result_data
    
    async def get_router_decision(self, research_question, chat_history=None):
        """Get router decision for which workflow to use"""
        print_separator("🔀 RESEARCH ROUTER")
        print("the current research question: {0}".format(research_question))
        
        # Use imported system prompt
        
        # Build user prompt with chat history context
        full_message = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]
        full_message.extend(chat_history or [])
        print(full_message)
        
        try:
            # Add timeout for router decision (15 seconds)
            router_start = time.time()
            
            # Create the OpenAI call with timeout
            async def make_openai_call():
                return self.client.chat.completions.create(
                    model=API_CONFIG["openai"]["model"],
                    messages=full_message,
                    tools=self.tools,
                    tool_choice="auto"
                )
            
            # Execute with 15-second timeout
            response = await asyncio.wait_for(make_openai_call(), timeout=15.0)
            
            router_time = time.time() - router_start
            
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                print(response.choices[0].message.tool_calls[0])
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)["query"]
                print(f"🤖 Router decided to use: {function_name} with query: {function_args}(took {router_time:.2f}s)")
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
    

    async def generate_research_queries(self, router_decision, router_query):
        """Generate multiple research queries for comprehensive analysis"""
        try:
            if router_decision == "Provide_a_List":
                SYSTEM_PROMPT = LIST_QUERY_GENERATION_PROMPT
            elif router_decision == "Search_the_Internet":
                SYSTEM_PROMPT = SEARCH_INTERNET_QUERY_GENERATION_PROMPT
            response = self.client.chat.completions.create(
                model=API_CONFIG["openai"]["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Research Question: {router_query}"}
                ],
                temperature=0.7
            )
            
            # Parse the response to extract queries
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for the start of a JSON array or object
                json_start = -1
                if '[' in response_text:
                    json_start = response_text.find('[')
                elif '{' in response_text:
                    json_start = response_text.find('{')

                if json_start != -1:
                    # Find the corresponding closing bracket/brace
                    if response_text[json_start] == '[':
                        json_end = response_text.rfind(']') + 1
                    else:
                        json_end = response_text.rfind('}') + 1
                    
                    json_str = response_text[json_start:json_end]
                    parsed_json = json.loads(json_str)
                    
                    if isinstance(parsed_json, list):
                        queries = parsed_json
                    elif isinstance(parsed_json, dict):
                        # If it's a dict, extract the values
                        queries = list(parsed_json.values())
                    else:
                        # Fallback for unexpected JSON types
                        queries = [router_query]
                else:
                    # Fallback if no JSON is found
                    queries = [line.strip().strip('"').strip("'") for line in response_text.split('\n') if line.strip()]

            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing query response: {e}")
                print(f"Response: {response_text}")
                # Fallback: use the original question
                queries = [router_query]
            
            print(f"✅ Generated {len(queries)} research queries:")
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
            
            return queries
            
        except Exception as e:
            print(f"❌ Error generating queries: {e}")
            # Fallback: use the original question
            return [router_query]
    
    async def Map_Queries_to_Websites(self, generated_queries):
        """Override the mapping function to use dynamic websites"""
        print_separator("🗺️  MAPPING QUERIES TO WEBSITES")
        
        # Use dynamic websites instead of imported ones
        all_websites = [site["domain"] for site in self.dynamic_websites]
        
        # Create mapping prompt using imported prompt
        from src.prompts import QUERY_MAPPING_PROMPT
        mapping_prompt = QUERY_MAPPING_PROMPT.format(
            available_websites="\n".join([f"- {site['domain']} ({site['name']})" for site in self.dynamic_websites]),
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

    async def execute_workflow(self, router_decision, research_question, queries):
        """Execute Provide_a_List workflow - comprehensive research approach"""
        print_separator("📋 EXECUTING {0} WORKFLOW".format(router_decision))
        workflow_start = time.time()
        
        # Phase 1: Map queries to relevant websites (queries already include chat history context)
        query_mappings = await self.Map_Queries_to_Websites(queries)
        
        # Phase 2: Prepare search tasks
        search_tasks = []
        
        # Add general web searches for all queries (already enhanced with chat history)
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
            if router_decision == "Provide_a_List":
                DOMAIN_PROMPT = PERPLEXITY_LIST_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_LIST_GENERAL_PROMPT
            elif router_decision == "Search_the_Internet":
                DOMAIN_PROMPT = PERPLEXITY_TIC_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_TIC_GENERAL_PROMPT

            if task["type"] == "general_web":
                return await self.async_perplexity_search(task["query"], prompt=GENERAL_PROMPT)
            else:  # domain_filtered
                return await self.async_perplexity_search(task["query"], domains=task["websites"], prompt=DOMAIN_PROMPT)
        
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
                    "citations": result.get("citations", []),
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
        
        total_time = time.time() - workflow_start
        
        # Compile final results object matching the response model
        result_data = {
            "request_id": str(uuid.uuid4()),
            "status": "completed",
            "message": "Research completed successfully.",
            "research_question": research_question,
            "workflow_type": router_decision,
            "query_mappings": query_mappings,
            "execution_summary": {
                "total_time_seconds": total_time,
                "total_searches": len(search_tasks),
                "general_searches": len([t for t in search_tasks if t["type"] == "general_web"]),
                "domain_searches": len([t for t in search_tasks if t["type"] == "domain_filtered"])
            },
            "search_results": processed_results,
            "timestamp": datetime.now().isoformat(),
            "processing_time": total_time
        }
        
        print_separator("📋 PROVIDE LIST WORKFLOW COMPLETE")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"📊 Total Searches: {len(search_tasks)}")
        print(f"🌐 General Web Searches: {len([t for t in search_tasks if t['type'] == 'general_web'])}")
        print(f"🏢 Domain-Filtered Searches: {len([t for t in search_tasks if t['type'] == 'domain_filtered'])}")
        
        return result_data


    async def route_research_request(self, research_question, chat_history=None):
        """Route research request to appropriate workflow based on router decision"""
        try:
            # Get router decision with chat history context
            router_answer = await self.get_router_decision(research_question, chat_history)
            router_decision = router_answer["type"]
            router_query = router_answer["content"]
            
            if router_decision == "Provide_a_List" or router_decision == "Search_the_Internet":
                # Generate multiple queries for comprehensive research
                queries = await self.generate_research_queries(router_decision, router_query)
                return await self.execute_workflow(router_decision, research_question, queries)
                
                
            elif router_decision == "direct_response":
                # Handle direct LLM response (no tool selected)
                print_separator("💬 DIRECT LLM RESPONSE")
                print(router_query)
                workflow_start = time.time()
                
                result_data = {
                    "request_id": str(uuid.uuid4()),
                    "status": "completed",
                    "message": "Direct LLM response provided.",
                    "research_question": research_question,
                    "workflow_type": "direct_response",
                    "execution_summary": {
                        "total_time_seconds": time.time() - workflow_start,
                        "response_type": "direct_llm_response"
                    },
                    "search_results": [{
                        "query": research_question,
                        "result": router_query,
                        "citations": [],
                        "extracted_links": [],
                        "status": "success",
                        "search_type": "direct_llm_response",
                        "websites": []
                    }],
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": time.time() - workflow_start
                }
                
                print(f"✅ Direct response provided in {time.time() - workflow_start:.2f} seconds")
                return result_data
                
            else:
                print(f"❌ Unknown tool selected: {router_decision}")
                return None
                
        except Exception as e:
            print(f"❌ Error in route_research_request: {str(e)}")
            return None

@app.post("/research", response_model=ResearchResultResponse)
async def start_research(request: ResearchRequest):
    """
    Start a new research request and get the results directly.
    This is a synchronous endpoint and may take a while to respond.
    """
    try:
        # Initialize dynamic workflow with provided domain metadata
        workflow = DynamicTICResearchWorkflow(request.domain_list_metadata)
        
        # Process the research request and wait for the result
        result = await workflow.route_research_request(request.research_question, request.chat_history)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Research failed - router timeout, no tool selected, or unknown tool"
            )
        
        return ResearchResultResponse(**result)

    except Exception as e:
        print(f"❌ Unhandled error in /research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint to confirm the API is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TIC Research API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 