📝 Description
An AI-native Reinforcement Learning environment designed for automated CRM data cleaning. This project simulates a professional data engineer's workflow, standardizing customer records across multiple database dialects (MariaDB, PostgreSQL, and SQLite) using an LLM-powered agent.

📂 Project Structure & Files
main.py: The entry point. It runs the FastAPI server that exposes the step, reset, and state endpoints.

env_logic.py: The "Engine." Contains the logic for database connections and the Regex-based reward system.

models.py: Defines the data structure (Pydantic models) for Actions and Observations.

openenv.yaml: The environment specification file containing metadata and task definitions for the benchmark.

Dockerfile: Instructions to containerize the application for deployment on Hugging Face Spaces.

requirements.txt: List of all Python dependencies (FastAPI, SQLAlchemy, etc.).

.env: Configuration for API keys, model names, and database connection strings.

inference.py: The baseline script used to run the AI agent against the environment to produce scores.

validate-submission.sh: A shell script to verify the API endpoints are functioning correctly in a Linux/Docker environment.

validate-submission.ps1: A PowerShell version for local Windows validation.

🛠️ Action Space
FIX_EMAIL: Corrects malformed emails (e.g., user[at]domain.com → user@domain.com).

FORMAT_PHONE: Standardizes numbers to E.164 format (e.g., +1234567890).

CAPITALIZE_NAME: Fixes improper casing and trailing whitespace (e.g., aditya → Aditya).

📊 Tasks & Difficulty
Easy (task_easy_email): Identify and fix a single malformed email address.

Medium (task_medium_phone): Perform multi-field cleaning involving phone formatting and name casing.

Hard (task_hard_duplicates): Full database standardization and advanced record logic.

🚀 Setup & Usage
Build the Container:

Bash
docker build -t crm-env .
Run the Environment:

Bash
docker run -p 7860:7860 crm-env
Run Baseline Inference:

Bash
python inference.py