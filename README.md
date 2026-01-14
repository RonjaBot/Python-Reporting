# Python Reporting – Pagila DWH

This project was created as part of the course **Data Management Analysis and Reporting**.
The goal is to build a small Python-based reporting application using the Pagila Data Warehouse.

## Overview
The application connects to a PostgreSQL data warehouse (`pagila_dwh`) and generates two interactive reports using Streamlit:

1. **Rentals by Film Category** (bar chart)  
2. **Rental Trends Over Time** (line chart)

Both reports support interactive filtering and summary statistics.

---

## Technology Stack
- Python 3.12
- PostgreSQL (Pagila DWH)
- Streamlit
- pandas
- plotly
- pg8000 (PostgreSQL driver)

---

## AI-Assisted Development

This project was developed using AI-assisted coding, as encouraged in the assignment.

### AI Tool Used
- **ChatGPT**

ChatGPT was used as a support tool for planning, debugging, and improving the reporting application.

### Main Prompts
The following prompts were used during development:

- *"Create a Streamlit app that connects to a PostgreSQL data warehouse (pagila_dwh) and displays two reports: rentals by film category and rental trends over time."*

- *"Write SQL queries to aggregate rental counts and revenue by film category and over time from a data warehouse."*

- *"I get connection and encoding errors when connecting Python to PostgreSQL on Windows. Explain the cause and suggest stable alternatives."*

- *"Add interactive filters (year, category, metric) to the Streamlit reports."*

- *"Improve the styling of Plotly charts and add meaningful summary statistics."*

### What Worked Well
- Using ChatGPT to scaffold the Streamlit application structure
- Support with SQL aggregation logic and query formulation
- Suggestions for improving chart styling and readability
- Help with debugging PostgreSQL connection issues

### Challenges
- PostgreSQL driver and encoding issues on Windows
- Debugging environment-related problems
- Ensuring that filters and summary statistics were analytically meaningful

Overall, ChatGPT was helpful for prototyping and problem-solving, but understanding the data model, validating SQL results, and making design decisions required manual work.

