# Intelligent Analytics Query Engine

An AI-powered analytics engine that converts natural-language business questions into structured, executable analytical queries and returns results with confidence scores and explanations.

## Overview

The Intelligent Analytics Query Engine enables users to ask questions such as:

- "What are the top 2 cities by profit?"
- "What were total sales in India for March?"
- "What is the average order value by region?"
- "Show revenue contribution by product category."
- "What is the year-over-year growth in revenue?"

The system translates natural language into a structured `QueryPlan`, validates the plan against a semantic registry and dataset schema, executes the analysis using pandas, and returns a JSON response.

## Architecture

```text
                    Natural Language Query
                              |
                              v
                    +-------------------+
                    |    FastAPI API    |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    |    LLM Planner    |
                    | Gemini / OpenRouter|
                    +-------------------+
                              |
                              v
                    +-------------------+
                    |     QueryPlan     |
                    |      Pydantic     |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | Semantic Registry |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | Query Validator   |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | Analytics Executor|
                    |     (pandas)      |
                    +-------------------+
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             Confidence Score     Explanation
                    |                   |
                    +---------+---------+
                              |
                              v
                         JSON Result
```

## Key Features

### Natural Language to QueryPlan

The LLM converts a natural-language question into a structured Pydantic `QueryPlan`.

The plan supports:

- Metrics
- Aggregations
- Dimensions
- Filters
- Time ranges
- Ranking
- Partitioned ranking
- Derived metrics
- Comparisons
- Secondary datasets

### Semantic Layer

A semantic registry defines the business meaning of analytics concepts.

| Business Term | Definition      |
| ------------- | --------------- |
| sales         | revenue         |
| income        | revenue         |
| earnings      | profit          |
| orders        | count(order_id) |
| AOV           | avg_order_value |

Revenue is defined as:

```text
quantity × unit_price × (1 - discount)
```

This semantic layer allows users to use business terminology without requiring knowledge of the underlying dataset schema.

### API Rate Limiting

The API uses Redis-backed rate limiting through SlowAPI to protect query and feedback endpoints from excessive requests.

Default limits:

- Query endpoint: 30 requests/minute
- Feedback endpoint: 60 requests/minute

The rate limiter uses the client's remote address as its key.

````text
Client
   |
   v
FastAPI
   |
   v
SlowAPI Rate Limiter
   |
   v
Redis
   |
   v
Analytics Query Engine

This allows the system to continue processing supported queries when an LLM provider is temporarily unavailable.

### Analytics Execution

The execution engine supports:

- SUM
- MEAN
- COUNT
- COUNT DISTINCT
- MIN
- MAX
- Filtering
- Grouping
- Ranking
- Partitioned ranking
- Average Order Value
- Derived calculations
- Year-over-year comparison

### Confidence and Explainability

Each query response includes:

- Confidence score between 0 and 1
- Structured query plan
- Human-readable explanation
- Analytical result

Example:

```json
{
  "query": "What are the top 2 cities by profit?",
  "planner": "gemini",
  "confidence": 1.0,
  "explanation": "Metrics: sum(profit). Grouped by: city. Ranked desc by profit.",
  "result": [
    {
      "city": "New York",
      "sum_profit": 200
    },
    {
      "city": "San Francisco",
      "sum_profit": 180
    }
  ]
}
````

### Feedback Loop

The API provides a feedback endpoint that records user feedback in `feedback_log.csv`.

This creates a foundation for future feedback-driven improvements to query planning and analytics quality.

## Project Structure

```text
intelligent-analytics-query-engine/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── planner.py
│   │   │   ├── prompts.py
│   │   │   ├── providers.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── analytics/
│   │   │   ├── executor.py
│   │   │   ├── operations.py
│   │   │   └── validator.py
│   │   │
│   │   ├── api/
│   │   │   └── routes.py
│   │   │
│   │   ├── confidence/
│   │   │   ├── scorer.py
│   │   │   └── explanation.py
│   │   │
│   │   ├── data/
│   │   │   ├── loader.py
│   │   │   └── registry.py
│   │   │
│   │   ├── feedback/
│   │   │   └── logger.py
│   │   │
│   │   └── main.py
│   │
│   └── tests/
│
├── dataset/
│   ├── sales_data.csv
│   ├── data_dictionary.json
│   └── nl_queries.json
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── architecture.md
├── README.md
└── .env.example
```

## API

### Health Check

```http
GET /health
```

### Execute Analytics Query

```http
POST /api/query
Content-Type: multipart/form-data
```

Parameters:

```text
query: natural-language analytics question
file: optional CSV dataset
```

If no dataset is uploaded, the configured default dataset is used.

### Submit Feedback

```http
POST /api/feedback
Content-Type: multipart/form-data
```

Parameters:

```text
query
result
feedback
```

Feedback is recorded in `feedback_log.csv`.

## Example Queries

### Total Sales

```text
Total sales in India for March
```

### Ranking

```text
What are the top 2 cities by profit?
```

### Aggregation

```text
What is the average order value by region?
```

### Contribution

```text
What is the sales contribution percentage by product category?
```

### Time Analysis

```text
What is the year-over-year growth in revenue?
```

### Advanced Ranking

```text
What is the top product in each region?
```

### Nested Analysis

```text
What is the revenue of the top 3 customers per region?
```

## Running Locally

### Backend

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables using `.env`:

```text
GEMINI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend

The frontend is a lightweight browser interface contained in the `frontend/` directory.

Open:

```text
frontend/index.html
```

in a browser while the FastAPI backend is running.

The interface sends natural-language queries to the backend and displays:

- Planner used
- Confidence score
- Explanation
- Generated query plan
- Analytical results

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- Pandas

### Generative AI

- Google Gemini
- OpenRouter
- Structured QueryPlan generation

### Infrastructure

- Redis
- SlowAPI
- Rate limiting

### Frontend

- HTML
- CSS
- JavaScript

### Data

- CSV
- JSON semantic registry

## Design Principles

### 1. Semantic Correctness

Business terminology is resolved through an explicit semantic registry before execution.

### 2. Structured Planning

LLM output is constrained to a typed Pydantic `QueryPlan` rather than allowing the model to directly generate executable Python or SQL.

### 3. Validation Before Execution

Generated plans are validated against the available dataset and semantic registry before analytics execution.

### 4. Provider Resilience

The system supports multiple LLM providers with a deterministic fallback planner.

### 5. Explainability

The system exposes the generated query plan, confidence score, and human-readable explanation alongside the result.

### 6. Separation of Concerns

The project separates:

```text
Natural Language Understanding
          ↓
Query Planning
          ↓
Semantic Validation
          ↓
Analytics Execution
          ↓
Confidence + Explanation
          ↓
API Response
```

This makes individual components independently testable and extensible.

## Example End-to-End Flow

For the question:

```text
What are the top 2 cities by profit?
```

The system performs the following steps:

```text
1. Receive natural-language query
              ↓
2. Resolve "profit" using semantic registry
              ↓
3. Generate structured QueryPlan
              ↓
4. Validate metric and dimension
              ↓
5. Group data by city
              ↓
6. Calculate total profit
              ↓
7. Rank cities by profit
              ↓
8. Select top 2
              ↓
9. Calculate confidence
              ↓
10. Generate explanation
              ↓
11. Return JSON response
```

## Security and Configuration

API keys are loaded from environment variables and should never be committed to the repository.

The `.env` file is excluded from version control.

Use `.env.example` as the configuration template.

```text
GEMINI_API_KEY=
OPENROUTER_API_KEY=
```

## Future Improvements

The architecture is designed to support additional capabilities such as:

- Celery workers for asynchronous query execution
- Persistent query history
- Feedback-driven planner improvement
- More advanced temporal expressions
- Target dataset integration
- Previous-period comparisons
- Query caching
- Streaming execution for large datasets
- Authentication and multi-user workspaces
- More sophisticated confidence calibration
- Interactive analytics visualizations

## Testing

The repository contains tests covering core components including:

- Query planning
- LLM planner integration
- Provider behavior
- Dataset registry
- Query validation
- Analytics execution

Run the test suite with:

```bash
pytest
```

## Submission

This project implements the **Intelligent Analytics Query Engine** assignment for the IIT Madras BS GenAI internship screening process.

The implementation focuses on converting natural-language analytics questions into structured plans, validating those plans against a semantic data layer, executing analytical operations, and returning explainable results.

## Author

**Drishya Garg**

#### 23f3001900

#### BS in Data Science And Applications

#### IIT Madras BS in Data Science and Programming
