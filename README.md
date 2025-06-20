# TIC Research System

Simplified research system for Testing, Inspection, and Certification (TIC) industry focused on import/export operations.

## 🏗️ Project Structure

```
tic-research-system/
├── tic_research.py              # Main TIC research workflow with router
├── tic_industry_websites.py     # 7 TIC websites configuration  
├── website_monitor.py           # Website monitoring service
├── config.py                    # Configuration and tools
├── prompts.py                   # Centralized prompt management
├── utils.py                     # Utility functions
├── api_services.py              # Perplexity API service
├── requirements.txt             # Dependencies
└── env_example.txt              # Environment variables template
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Copy `env_example.txt` to `.env` and add your API keys:
```
OPENAI_API_KEY=sk-your-openai-key-here
PERPLEXITY_API_KEY=your-perplexity-key-here
```

### 3. Run TIC Research
```bash
python tic_research.py
```

## 🔄 How It Works

**Smart Router System:**
The system uses an AI router to decide between three research approaches:

### **Path A: Provide_a_List Workflow**
1. **User provides question**
2. **AI generates search queries** using OpenAI
3. **AI maps queries to relevant websites** using intelligent matching
4. **Execute searches in parallel**:
   - General web search for all queries
   - Domain-filtered search for mapped queries
5. **Combine results** using OpenAI for final report

### **Path B: TIC_Specific_Questions Workflow**
1. **User provides question + target domains**
2. **Direct web search** using Perplexity
3. **Domain-filtered searches** for each target domain
4. **Return structured results** with citations

### **Path C: Direct_Answer Workflow**
- **LLM provides direct answer** via function tool
- **No external research needed**
- **Structured response format**

### **Tool Selection Logic**
The AI router automatically chooses the best approach based on:
- Question complexity
- Need for comprehensive research
- Confidence level in direct knowledge

## 🌐 TIC Websites Monitored

- cbp.gov (U.S. Customs)
- cosmos-standard.org (Organic certification)
- global-standard.org (Textile standards)
- madesafe.org (Non-toxic certification)
- natrue.org (Natural cosmetics)
- usda.gov (USDA organic)
- vegansociety.com (Vegan certification)

## 💡 Example Questions

- "What certifications are required to export honey from India to the USA?"
- "What are organic certification requirements for cosmetics?"
- "What are USDA organic standards for food imports?"

## ⚡ Performance

- True parallel execution using async/await
- 2-4 minutes for complete TIC research
- Checks 7 websites + web search simultaneously
- Professional reports with citations
- Smart routing for optimal research approach

## 🛠️ Customization

Edit `tic_research.py` to modify the router criteria in the system prompt.
Edit `tic_industry_websites.py` to modify the 7 websites or add/remove sites as needed. 