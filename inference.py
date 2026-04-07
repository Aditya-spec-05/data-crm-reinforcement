import asyncio
import os
import textwrap
import json
from typing import List, Optional
from openai import OpenAI
import httpx
from dotenv import load_dotenv  # 1. Add this import

load_dotenv()  # 2. Add this line before anything else
# --- CONFIGURATION ---
# These pull from your .env file or Hugging Face Secrets
API_URL = os.getenv("API_URL", "https://adityaselvam-data-crm-cleaner.hf.space")
API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/llama-3.2-3b-instruct:free")

# Task metadata (Must match openenv.yaml)
TASK_NAME = os.getenv("TASK_NAME", "task_easy_email")
BENCHMARK = os.getenv("BENCHMARK", "datascan_crm_v1")
MAX_STEPS =  30
SUCCESS_THRESHOLD = 0.5

# Enhanced prompt including the DELETE_DUPLICATE action
SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a Data Quality Agent. Your goal is to clean a CRM database.
    Available Actions:
    1. FIX_EMAIL: Fix malformed emails (e.g., 'user[at]gmail.com' -> 'user@gmail.com').
    2. FORMAT_PHONE: Ensure phones start with '+' (e.g., '12345' -> '+12345').
    3. CAPITALIZE_NAME: Convert names to Title Case (e.g., 'aditya' -> 'Aditya').
    4. DELETE_DUPLICATE: Remove a record if it is a duplicate of another.

    You MUST respond in valid JSON format only:
    {"record_id": 1, "action_type": "FIX_EMAIL", "new_value": "correct@email.com"}
    """
).strip()

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    # Ensure action string is compact for logging
    clean_action = action.replace("\n", "").replace(" ", "")
    print(f"[STEP] step={step} action={clean_action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def run_agent():
    # OpenAI client configured for OpenRouter
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    async with httpx.AsyncClient(timeout=45.0) as http_client:
        history: List[float] = []
        log_start(TASK_NAME, BENCHMARK, MODEL_NAME)
        
        try:
            # 1. RESET
            resp = await http_client.post(f"{API_URL}/reset?task_id={TASK_NAME}")
            resp.raise_for_status()
            observation = resp.json()["observation"]
            
            for step in range(1, MAX_STEPS + 1):
                # 2. INFERENCE
                user_msg = f"Current State: {observation}. What is your next cleaning action?"
                
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg}
                    ],
                    response_format={ "type": "json_object" }
                )
                
                action_text = completion.choices[0].message.content
                action_data = json.loads(action_text)

                # 3. STEP
                step_resp = await http_client.post(f"{API_URL}/step", json=action_data)
                step_resp.raise_for_status()
                result = step_resp.json()
                
                reward = result["reward"]
                done = result["done"]
                observation = result["observation"]
                
                history.append(reward)
                log_step(step, action_text, reward, done, None)
                
                if done:
                    break

            # 4. FINAL SCORE
            total_reward = sum(history)
            final_score = min(max(total_reward, 0.0), 1.0)
            success = final_score >= SUCCESS_THRESHOLD
            log_end(success, len(history), final_score, history)

        except Exception as e:
            log_end(False, len(history), 0.0, history)
            print(f"[DEBUG] Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_agent())