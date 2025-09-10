from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import uvicorn
import logging
import asyncio
import hashlib
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Caching for performance and API optimization
relevance_cache = {}  # Cache relevance check responses
response_cache = {}   # Cache full responses for identical questions

@lru_cache(maxsize=1)
def get_cached_schema():
    """Cache the database schema to avoid repeated calls."""
    return db.get_table_info()

app = FastAPI(title="Text-to-SQL PoC", description="A proof-of-concept Text-to-SQL system for port financials and operations.")

class QueryRequest(BaseModel):
    question: str

# Check if database exists
if not os.path.exists('business_data.db'):
    logging.error("Database file 'business_data.db' not found. Please run load_data.py first.")
    raise FileNotFoundError("Database not found")

# Check API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logging.error("GOOGLE_API_KEY not found in environment variables.")
    raise ValueError("API key not set")

db = SQLDatabase.from_uri("sqlite:///business_data.db")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0)

# Create toolkit (no filtering needed for create_sql_agent)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create the SQL agent with a simple system message
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="openai-tools",  # Or "zero-shot-react-description" if preferred
    prefix=f"You are an AI assistant that answers questions about port financials (e.g., balance sheets, P&L, ROCE) and operations (e.g., cargo volumes, containers, RORO). The database schema is:\n{get_cached_schema()}\n\nAlways generate SQL queries based on this schema. Provide detailed, explanatory responses, including the SQL query used and a summary of the data. If the question is not related, politely decline.\n\nExamples:\n- For EBIT at a port: SELECT value FROM roce_internal WHERE port = 'APSEZ' AND line_item = 'EBIT' AND period = '2024-25';\n- For cargo volume: SELECT SUM(value) FROM volumes WHERE port = 'Mundra' AND period = '2024-25';\n- For revenue: SELECT value FROM consolidated_pnl WHERE \"Line Item\" = 'Revenue from Operation' AND \"Period\" = '2024-25';"
)

logging.info("Application started successfully with optimized SQL agent.")

@app.post("/query")
async def query_database(request: QueryRequest):
    question = request.question.strip()
    
    # Check response cache first
    question_hash = hashlib.md5(question.encode()).hexdigest()
    if question_hash in response_cache:
        logging.info("Returning cached response for question.")
        return {"response": response_cache[question_hash]}
    
    # Handle greetings
    greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
    if question.lower() in greetings or any(greet in question.lower() for greet in greetings):
        response = "Hello! I'm here to help with questions about port financials and operations. What would you like to know?"
        response_cache[question_hash] = response
        return {"response": response}
    
    # Simple relevance check using LLM (with caching and error handling)
    relevance_prompt = f"Is this question about port financials or operations? Answer 'yes' or 'no': {question}"
    relevance_hash = hashlib.md5(relevance_prompt.encode()).hexdigest()
    
    if relevance_hash in relevance_cache:
        relevance_response = relevance_cache[relevance_hash]
        logging.info("Using cached relevance check.")
    else:
        try:
            relevance_response = llm.invoke([HumanMessage(content=relevance_prompt)]).content.lower()
            relevance_cache[relevance_hash] = relevance_response
        except Exception as e:
            error_str = str(e)
            if "ResourceExhausted" in error_str or "429" in error_str or "quota" in error_str.lower():
                logging.warning("Gemini API quota exceeded. Skipping relevance check and proceeding with query.")
                relevance_response = "yes"  # Assume relevant if quota exceeded
            else:
                logging.warning(f"Error in relevance check: {e}")
                relevance_response = "yes"  # Assume relevant if check fails
    
    if "no" in relevance_response:
        response = "I'm sorry, I can only answer questions about port financials and operations."
        response_cache[question_hash] = response
        return {"response": response}
    
    try:
        # Run the agent
        result = agent_executor.invoke({"input": question})
        # Extract the final answer
        final_answer = result.get('output', str(result)) if isinstance(result, dict) else str(result)
        
        # Extract SQL query from intermediate steps
        sql_query = "Generated by SQL Agent"
        intermediate_steps = result.get('intermediate_steps', [])
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step
                if hasattr(action, 'tool') and action.tool == 'sql_db_query' and hasattr(action, 'log'):
                    log = action.log
                    if 'Action Input:' in log:
                        input_part = log.split('Action Input:', 1)[1].strip()
                        cleaned_query = input_part.replace('```sql', '').replace('```', '').strip()
                        if 'SELECT' in cleaned_query.upper() or 'select' in cleaned_query.upper():
                            sql_query = cleaned_query
        
        # Ensure natural language response
        if final_answer and final_answer.replace(',', '').replace('.', '').replace(' ', '').isdigit():
            final_answer = f"The result is {final_answer}."
        
        # Include SQL query in the response for transparency
        if sql_query != "Generated by SQL Agent":
            final_answer += f"\n\nSQL Query Used: {sql_query}"
        
        logging.info(f"Generated SQL: {sql_query}")
        logging.info(f"Final Answer: {final_answer}")
        
        # Cache the response
        response_cache[question_hash] = final_answer
        
        return {"response": final_answer}
    except Exception as e:
        error_str = str(e)
        if "ResourceExhausted" in error_str or "429" in error_str or "quota" in error_str.lower():
            logging.error("Gemini API quota exceeded during query processing.")
            response = "Sorry, the AI service quota has been exceeded. Please check your Google Cloud billing or wait for the quota to reset (typically daily for free tier)."
        else:
            logging.error(f"Exception occurred: {error_str}", exc_info=True)
            response = "I'm sorry, I encountered an error processing your question. Please try rephrasing."
        
        # Cache error responses too
        response_cache[question_hash] = response
        return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
