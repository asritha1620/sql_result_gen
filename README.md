# Text-to-SQL Proof of Concept

## Overview
This project is a proof-of-concept (PoC) Text-to-SQL system designed to answer natural language questions about business data. It uses a FastAPI backend for the API and a Streamlit frontend for the user interface. The system interprets user questions, generates appropriate SQL queries, executes them against a SQLite database, and returns concise natural language responses.

The data includes:
- **Financial Data**: Quarterly financial statements (revenue, net income, assets, liabilities) and annual performance metrics.
- **Operational Data**: Cargo volumes handled at various international ports over time.

## Setup Instructions
1. **Clone or Download the Repository**: Ensure all files are in the project directory.

2. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   - Create a `.env` file in the root directory.
   - Add your Google Gemini API key:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```

4. **Load Data into Database**:
   ```
   python load_data.py
   ```
   This creates `business_data.db` and populates it with mock data from the CSV files.

5. **Run the FastAPI Backend**:
   ```
   python app.py
   ```
   The API will be available at `http://localhost:8000`.

6. **Run the Streamlit UI** (in a separate terminal):
   ```
   streamlit run ui.py
   ```
   The UI will open in your browser.

## Dependencies
The project requires the following Python packages (listed in `requirements.txt`):
- `fastapi`: For the backend API.
- `uvicorn`: ASGI server for FastAPI.
- `streamlit`: For the frontend UI.
- `langchain`: For the AI agent framework.
- `langchain-google-genai`: For integration with Google Gemini.
- `langchain-community`: For community tools like SQLDatabase.
- `python-dotenv`: For environment variable management.
- `pandas`: For data loading from CSV.
- `requests`: For API calls in the UI.

Install all via `pip install -r requirements.txt`.

## Database Schema
The SQLite database `business_data.db` contains the following tables:

- **quarterly_financial**:
  - `year` (INTEGER): The year of the financial data.
  - `quarter` (TEXT): The quarter (e.g., Q1, Q2).
  - `revenue` (REAL): Revenue for the quarter.
  - `net_income` (REAL): Net income for the quarter.
  - `assets` (REAL): Total assets.
  - `liabilities` (REAL): Total liabilities.

- **annual_financial**:
  - `year` (INTEGER): The year.
  - `metric` (TEXT): The metric name (e.g., total_revenue).
  - `value` (REAL): The value of the metric.

- **operational_cargo**:
  - `year` (INTEGER): The year.
  - `quarter` (TEXT): The quarter.
  - `port` (TEXT): The port name.
  - `volume` (REAL): Cargo volume handled.

## Design Choices
- **AI/ML Approach**: Used LangChain's `create_sql_agent` with Google's Gemini 1.5 Flash for natural language to SQL conversion. The agent uses a zero-shot react description approach for generating and executing SQL queries against the database. It returns intermediate steps, allowing us to extract the generated SQL and the final natural language response.
- **Database**: SQLite for simplicity and portability.
- **Backend**: FastAPI for a robust API with automatic documentation.
- **Frontend**: Streamlit for a quick and easy-to-use web interface with chat history.
- **Prompting Strategy**: The agent uses built-in prompts optimized for SQL tasks, with domain-specific context provided through the database schema.

## Limitations and Known Issues
- Requires an active Google Gemini API key with sufficient quota; the free tier has a rate limit of 15 requests per minute.
- The system uses mock data; in production, real data sources would be needed.
- Error handling is basic; complex queries might fail or produce incorrect SQL.
- The model may not handle very ambiguous questions well.
- No fine-tuning of the model; relies on prompt engineering.
- Assumes the FastAPI server is running on localhost:8000 for the Streamlit UI to work.

## Usage
- Enter a natural language question in the Streamlit UI, such as "What was the total revenue in 2023?" or "How much cargo was handled at New York in Q1 2024?"
- The system will provide a natural language response based on the data.
- If the question is outside the scope, it will respond accordingly.
