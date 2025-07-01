"""
Core TIC research workflows
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..services import OpenAIService, PerplexityService
from ..models.domain import DomainMetadata
from ..utils.helpers import print_separator


class TICResearchWorkflow:
    """Base TIC research workflow"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.perplexity_service = PerplexityService()
    
    async def route_research_request(self, research_question: str, chat_history: Optional[List[Dict]] = None) -> Optional[Dict[str, Any]]:
        """Route research request to appropriate workflow based on router decision"""
        # print("[WORKFLOW] route_research_request called with:", research_question, chat_history)
        try:
            # Get router decision with chat history context
            router_answer = await self.openai_service.get_router_decision(research_question, chat_history)
            if not router_answer:
                return None
                
            router_decision = router_answer["type"]
            router_query = router_answer["content"]
            
            print("[WORKFLOW] Router answer:", router_answer)
            
            if router_decision == "Provide_a_List" or router_decision == "Search_the_Internet":
                # Generate multiple queries for comprehensive research
                print("[WORKFLOW] Provide_a_List or Search_the_Internet selected. Generating queries...")
                queries = await self.openai_service.generate_research_queries(router_decision, router_query)
                print("[WORKFLOW] Queries generated:", queries)
                result = await self.execute_workflow(router_decision, research_question, queries)
                print("[WORKFLOW] execute_workflow result:", result)
                return result
                
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
    
    async def execute_workflow(self, router_decision: str, research_question: str, queries: List[str]) -> Dict[str, Any]:
        """Execute research workflow - to be implemented by subclasses"""
        print("[WORKFLOW] execute_workflow called with:", router_decision, research_question, queries)
        raise NotImplementedError("Subclasses must implement execute_workflow")


class DynamicTICResearchWorkflow(TICResearchWorkflow):
    """Extended TIC research workflow that can use dynamic domain metadata"""
    
    def __init__(self, domain_metadata: List[DomainMetadata]):
        super().__init__()
        self.domain_metadata = domain_metadata
        self.dynamic_websites = self._convert_metadata_to_websites()
    
    def _convert_metadata_to_websites(self) -> List[Dict[str, Any]]:
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
    

    async def execute_workflow(self, router_decision: str, research_question: str, search_tasks: List[str]) -> Dict[str, Any]:
        """Execute research workflow with dynamic domain metadata"""
        print_separator("📋 EXECUTING {0} WORKFLOW".format(router_decision))
        workflow_start = time.time()
        
        # Debug: Print the queries to be mapped
        
        # Phase 1: Map queries to relevant websites
        
        # Phase 3: Execute all searches in parallel
        print_separator("Executing Parallel Searches")
        
        async def execute_search_task(task: Dict[str, Any]) -> Dict[str, Any]:
            from ..config import (
                PERPLEXITY_LIST_DOMAIN_PROMPT, PERPLEXITY_LIST_GENERAL_PROMPT,
                PERPLEXITY_TIC_DOMAIN_PROMPT, PERPLEXITY_TIC_GENERAL_PROMPT
            )
            
            if router_decision == "Provide_a_List":
                DOMAIN_PROMPT = PERPLEXITY_LIST_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_LIST_GENERAL_PROMPT
                structured_output = True
            elif router_decision == "Search_the_Internet":
                DOMAIN_PROMPT = PERPLEXITY_TIC_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_TIC_GENERAL_PROMPT
                structured_output = False
            else:
                DOMAIN_PROMPT = PERPLEXITY_TIC_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_TIC_GENERAL_PROMPT
                structured_output = False

            if task["type"] == "general_web":
                return await self.perplexity_service.search(
                    task["query"], 
                    prompt=GENERAL_PROMPT, 
                    use_structured_output=structured_output
                )
            else:  # domain_filtered
                return await self.perplexity_service.search(
                    task["query"], 
                    domains=task["websites"], 
                    prompt=DOMAIN_PROMPT, 
                    use_structured_output=structured_output
                )
        
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
                    "extracted_links": self.perplexity_service.extract_links_from_content(result["content"]),
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
        
        # Compile final results object
        result_data = {
            "request_id": str(uuid.uuid4()),
            "status": "completed",
            "message": "Research completed successfully.",
            "research_question": research_question,
            "workflow_type": router_decision,

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
        
        print_separator("📋 WORKFLOW COMPLETE")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"📊 Total Searches: {len(search_tasks)}")
        print(f"🌐 General Web Searches: {len([t for t in search_tasks if t['type'] == 'general_web'])}")
        print(f"🏢 Domain-Filtered Searches: {len([t for t in search_tasks if t['type'] == 'domain_filtered'])}")
        
        return result_data

    async def route_research_request_with_progress(
        self, 
        research_question: str, 
        chat_history: Optional[List[Dict]] = None,
        progress_callback=None
    ) -> Optional[Dict[str, Any]]:
        """Route research request with progress callbacks for streaming"""
        print("[WORKFLOW] route_research_request_with_progress called with:", research_question, chat_history)
        
        try:
            # Send router decision progress
            if progress_callback:
                await progress_callback("router_decision", {"message": "Determining research workflow..."})
            
            # Get router decision with chat history context
            router_answer = await self.openai_service.get_router_decision(research_question, chat_history)
            if not router_answer:
                return None
                
            router_decision = router_answer["type"]
            router_query = router_answer["content"]
            
            print("[WORKFLOW] Router answer:", router_answer)
            
            if router_decision == "Provide_a_List" or router_decision == "Search_the_Internet":
                # Send query generation progress
                if progress_callback:
                    await progress_callback("query_generation", {"message": "Generating research queries..."})
                
                # Generate multiple queries for comprehensive research
                print("[WORKFLOW] Provide_a_List or Search_the_Internet selected. Generating queries...")
                queries = await self.openai_service.generate_research_queries(router_decision, router_query)
                print("[WORKFLOW] Queries generated:", queries)
                
                # Send search progress
                if progress_callback:
                    await progress_callback("search_progress", {
                        "message": f"Starting {len(queries)} research queries...",
                        "total_queries": len(queries)
                    })
                
                result = await self.execute_workflow_with_progress(router_decision, research_question, queries, progress_callback)
                print("[WORKFLOW] execute_workflow result:", result)
                return result
                
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
            print(f"❌ Error in route_research_request_with_progress: {str(e)}")
            return None

    async def execute_workflow_with_progress(
        self, 
        router_decision: str, 
        research_question: str, 
        queries: List[str],
        progress_callback=None
    ) -> Dict[str, Any]:
        """Execute research workflow with progress callbacks"""
        print_separator("📋 EXECUTING {0} WORKFLOW WITH PROGRESS".format(router_decision))
        workflow_start = time.time()
        
        # Debug: Print the queries to be mapped
        print(f"[DEBUG] Queries to be mapped ({len(queries)}): {queries}")
        
        # Phase 1: Map queries to relevant websites
        if progress_callback:
            await progress_callback("query_mapping", {"message": "Mapping queries to relevant websites..."})
        
        query_mappings = await self.openai_service.map_queries_to_websites(queries, self.dynamic_websites)
        
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
                    "websites": mapping["websites"]
                })
        
        # Phase 3: Execute all searches in parallel with progress updates
        print_separator("Executing Parallel Searches")
        
        if progress_callback:
            await progress_callback("search_progress", {
                "message": f"Executing {len(search_tasks)} searches in parallel...",
                "total_searches": len(search_tasks)
            })
        
        async def execute_search_task(task: Dict[str, Any]) -> Dict[str, Any]:
            from ..config import (
                PERPLEXITY_LIST_DOMAIN_PROMPT, PERPLEXITY_LIST_GENERAL_PROMPT,
                PERPLEXITY_TIC_DOMAIN_PROMPT, PERPLEXITY_TIC_GENERAL_PROMPT
            )
            
            if router_decision == "Provide_a_List":
                DOMAIN_PROMPT = PERPLEXITY_LIST_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_LIST_GENERAL_PROMPT
                structured_output = True
            elif router_decision == "Search_the_Internet":
                DOMAIN_PROMPT = PERPLEXITY_TIC_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_TIC_GENERAL_PROMPT
                structured_output = False
            else:
                DOMAIN_PROMPT = PERPLEXITY_TIC_DOMAIN_PROMPT
                GENERAL_PROMPT = PERPLEXITY_TIC_GENERAL_PROMPT
                structured_output = False

            if task["type"] == "general_web":
                return await self.perplexity_service.search(
                    task["query"], 
                    prompt=GENERAL_PROMPT, 
                    use_structured_output=structured_output
                )
            else:  # domain_filtered
                return await self.perplexity_service.search(
                    task["query"], 
                    domains=task["websites"], 
                    prompt=DOMAIN_PROMPT, 
                    use_structured_output=structured_output
                )
        
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
                    "extracted_links": self.perplexity_service.extract_links_from_content(result["content"]),
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
        
        # Compile final results object
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
        
        print_separator("📋 WORKFLOW COMPLETE")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"📊 Total Searches: {len(search_tasks)}")
        print(f"🌐 General Web Searches: {len([t for t in search_tasks if t['type'] == 'general_web'])}")
        print(f"🏢 Domain-Filtered Searches: {len([t for t in search_tasks if t['type'] == 'domain_filtered'])}")
        
        return result_data 