from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import uvicorn
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI(title="Text-to-SQL PoC", description="A proof-of-concept Text-to-SQL system for business data.")

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

# Create toolkit and filter tools to reduce API calls
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()
# Remove query_checker and schema tools to reduce API calls
tools = [t for t in tools if t.name not in ['sql_db_query_checker', 'sql_db_schema']]

tool_names = [t.name for t in tools]
format_instructions = f"""Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of {tool_names}
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""

# Create custom agent with schema in prefix to avoid schema calls
prefix = f"You are an agent that can query a SQL database. The database has the following tables:\n{db.get_table_info()}\n\nImportant instructions:\n- When using the sql_db_query tool, provide the SQL query as plain text without any markdown formatting like ```sql or code blocks.\n- Always provide the final answer in natural language, explaining the result based on the data retrieved. Do not output raw numbers or data without context.\n\nExamples for complex queries:\n- Aggregations: For 'What is the average revenue in 2023?', use SELECT AVG(revenue) FROM quarterly_financial WHERE year = 2023;\n- Joins: For 'Compare revenue and cargo volume in Q1 2023', use SELECT q.revenue, o.volume FROM quarterly_financial q INNER JOIN operational_cargo o ON q.year = o.year AND q.quarter = o.quarter WHERE q.year = 2023 AND q.quarter = 'Q1';\n- Subqueries: For 'Ports with cargo above average in 2023', use SELECT port, volume FROM operational_cargo WHERE year = 2023 AND volume > (SELECT AVG(volume) FROM operational_cargo WHERE year = 2023);\n- Cross-domain: For 'Total revenue per cargo volume in 2023', combine tables using JOIN and GROUP BY.\n\n{format_instructions}\n\n"
suffix = "Begin!\n\nQuestion: {input}\nThought: {agent_scratchpad}"

agent = ZeroShotAgent.from_llm_and_tools(
    llm=llm,
    tools=tools,
    prefix=prefix,
    suffix=suffix
)

# Create agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
    return_intermediate_steps=True
)

logging.info("Application started successfully with optimized SQL agent.")

@app.post("/query")
async def query(request: QueryRequest):
    question = request.question
    logging.info(f"Received question: {question}")
    
    if not question.strip():
        logging.warning("Empty question received")
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check for greetings
    words = question.lower().split()
    if len(words) <= 3:
        greetings = ['hi', 'hello', 'hey', 'good', 'morning', 'afternoon', 'evening', 'thanks', 'thank']
        if any(word in greetings for word in words):
            logging.info("Detected greeting")
            return {"response": "Hello! How can I help you with questions about company finance or cargo operations?"}
    
    # Check if question is relevant using LLM
    try:
        response = await asyncio.to_thread(llm.invoke, [HumanMessage(content=f"""Determine if this question is about company finance or cargo operations.
Answer only 'yes' or 'no':

Question: {question}
Answer:""")])
        answer = response.content.strip().lower()
        is_relevant = answer == 'yes'
    except Exception as e:
        logging.warning(f"Error in relevance check: {e}")
        is_relevant = True  # Assume relevant
    
    if not is_relevant:
        logging.info("Question determined to be outside scope by LLM")
        return {"response": "I'm sorry, I can only answer questions about company finance and cargo operations."}
    
    try:
        logging.info("Running optimized SQL agent...")
        result = await asyncio.to_thread(agent_executor, question)
        logging.info("Agent executed successfully")
        
        final_answer = result.get('output', str(result))
        intermediate_steps = result.get('intermediate_steps', [])
        
        logging.info(f"Raw agent output: {final_answer}")
        
        # Extract SQL query from intermediate steps (for logging only, not returned)
        sql_query = "Generated by SQL Agent"
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
        
        logging.info(f"Generated SQL: {sql_query}")
        logging.info(f"Final Answer: {final_answer}")
        
        return {"response": final_answer}
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg or "RateLimitError" in error_msg or "ResourceExhausted" in error_msg or "429" in error_msg:
            logging.error("Gemini API quota exceeded. Please check your Google Cloud billing or wait for the rate limit to reset.")
            raise HTTPException(status_code=429, detail="Gemini API quota exceeded. Please check your Google Cloud billing or wait for the rate limit to reset.")
        logging.error(f"Exception occurred: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail="I'm sorry, I can only answer questions about company finance and cargo operations.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
