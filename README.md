# Text-to-SQL Proof of Concept

## Overview
This project is a proof-of-concept (PoC) Text-to-SQL system designed to answer natural language questions about port financials and operations. It uses a FastAPI backend for the API and a Streamlit frontend for the user interface. The system interprets user questions, generates appropriate SQL queries, executes them against a SQLite database, and returns concise natural language responses.

The data includes:
- **Balance Sheet**: Financial position data including assets, liabilities, etc.
- **Cash Flow Statement**: Cash inflows and outflows.
- **Consolidated P&L**: Profit and loss statements.
- **Quarterly P&L**: Detailed quarterly financials.
- **ROCE External/Internal**: Return on Capital Employed metrics.
- **Volumes**: Cargo volumes at various ports.
- **Containers**: Container handling data.
- **RORO**: Roll-on/Roll-off vehicle data.

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

- **balance_sheet**:
  - `line_item` (VARCHAR(255)): The financial line item.
  - `category` (VARCHAR(50)): Category (e.g., ASSETS).
  - `subcategory` (VARCHAR(100)): Subcategory.
  - `subsubcategory` (VARCHAR(100)): Sub-subcategory.
  - `period` (VARCHAR(20)): Period (e.g., 2024-25).
  - `value` (REAL): The value.

- **cash_flow_statement**:
  - `item` (VARCHAR(255)): The cash flow item.
  - `category` (VARCHAR(100)): Category.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.

- **roce_external**:
  - `particular` (VARCHAR(100)): The particular metric.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.

- **roce_internal**:
  - `category` (VARCHAR(50)): Category.
  - `port` (VARCHAR(50)): Port name.
  - `line_item` (VARCHAR(100)): Line item.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.

- **quarterly_pnl**:
  - `item` (VARCHAR(255)): The item.
  - `category` (VARCHAR(50)): Category.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.
  - `period_type` (VARCHAR(20)): Period type.

- **consolidated_pnl**:
  - `line_item` (VARCHAR(100)): Line item.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.

- **volumes**:
  - `port` (VARCHAR(50)): Port name.
  - `state` (VARCHAR(50)): State.
  - `commodity` (VARCHAR(50)): Commodity.
  - `entity` (VARCHAR(50)): Entity.
  - `type` (VARCHAR(20)): Type.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The volume.

- **containers**:
  - `port` (VARCHAR(50)): Port name.
  - `entity` (VARCHAR(50)): Entity.
  - `type` (VARCHAR(20)): Type.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.

- **roro**:
  - `port` (VARCHAR(50)): Port name.
  - `type` (VARCHAR(20)): Type.
  - `period` (VARCHAR(20)): Period.
  - `value` (REAL): The value.
  - `number_of_cars` (INTEGER): Number of cars.

Indexes are created on key join columns (e.g., `period`, `port`) for improved query performance.

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
- Enter a natural language question in the Streamlit UI, such as "What is the EBIT for APSEZ in 2024-25?" or "How much cargo volume was handled at Mundra in 2024-25?"
- The system will provide a natural language response based on the data.
- If the question is outside the scope, it will respond accordingly.
