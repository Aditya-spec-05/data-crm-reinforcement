import asyncio
import os
import textwrap
import json
from typing import List, Optional
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# 1. MANDATORY: The validator injects API_BASE_URL and API_KEY. 
# We MUST prioritize these to pass the proxy check.
API_BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("HF_TOKEN")

# API_URL is your Hugging Face space URL
API_URL = os.getenv("API_URL", "https://adityaselvam-data-crm-cleaner.hf.space")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/llama-3.2-3b-instruct:free")

TASK_NAME = os.getenv("TASK_NAME", "task_easy_email")
BENCHMARK = os.getenv("BENCHMARK", "datascan_crm_v1")
MAX_STEPS = 30
SUCCESS_THRESHOLD = 0.5

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
    clean_action = action.replace("\n", "").replace(" ", "")
    print(f"[STEP] step={step} action={clean_action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def run_agent():
    # Initialize OpenAI client using the proxy URL and Key
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    async with httpx.AsyncClient(timeout=45.0) as http_client:
        history: List[float] = []
        log_start(TASK_NAME, BENCHMARK, MODEL_NAME)
        
        try:
            resp = await http_client.post(f"{API_URL}/reset?task_id={TASK_NAME}")
            resp.raise_for_status()
            observation = resp.json()["observation"]
            
            for step in range(1, MAX_STEPS + 1):
                user_msg = f"Current State: {observation}. What is your next cleaning action?"
                
                # The call MUST go through client (OpenAI) to hit the proxy
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

            total_reward = sum(history)
            
            # Phase 2 requires scores strictly between 0 and 1.
            # We add a tiny epsilon to avoid exactly 0.0 or 1.0
            final_score = min(max(total_reward, 0.01), 0.99)
            
            success = final_score >= SUCCESS_THRESHOLD
            log_end(success, len(history), final_score, history)

        except Exception as e:
            log_end(False, len(history), 0.01, history)
            print(f"[DEBUG] Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_agent())
