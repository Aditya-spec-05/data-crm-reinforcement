import os
import re # Added for Regex
from sqlalchemy import create_engine, text
from typing import Tuple, Dict, Any
from models import CRMAction, CRMObservation

class CRMEnvLogic:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///crm.db")
        self.engine = create_engine(self.db_url)
        self.max_steps = 20 # Increased to handle more data
        self.current_step = 0
        
        # Regex Patterns for validation
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.phone_pattern = r'^\+\d{7,15}$' # Starts with +, then 7-15 digits

    def reset_db(self, task_id: str = "task_easy_email"):
        self.current_step = 0
        with self.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS customers"))
            conn.execute(text("""
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY, 
                    name VARCHAR(255), 
                    email VARCHAR(255), 
                    phone VARCHAR(255), 
                    status VARCHAR(50)
                )
            """))
            
            # You can now add as much messy data here as you want!
            data = [
                {"id": 1, "name": 'aditya', "email": 'aditya[at]gmail.com', "phone": '12345', "status": 'dirty'},
                {"id": 2, "name": 'JOHN DOE', "email": 'john.doe@gmail', "phone": '9876543210', "status": 'dirty'},
                {"id": 3, "name": '  alice smith  ', "email": 'alice.s@work.co', "phone": '000-000', "status": 'dirty'},
                {"id": 4, "name": 'bob', "email": 'bob.messy#email.com', "phone": '5551234', "status": 'dirty'}
            ]
            
            for row in data:
                conn.execute(text("INSERT INTO customers (id, name, email, phone, status) VALUES (:id, :name, :email, :phone, :status)"), row)
        
        return self.get_observation("Task started: " + task_id)

    def step(self, action: CRMAction) -> Tuple[CRMObservation, float, bool]:
        self.current_step += 1
        reward = 0.0
        
        with self.engine.begin() as conn:
            # 1. Update the Database
            if action.action_type == "FIX_EMAIL":
                conn.execute(text("UPDATE customers SET email = :val, status = 'cleaned' WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})
            elif action.action_type == "FORMAT_PHONE":
                conn.execute(text("UPDATE customers SET phone = :val WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})
            elif action.action_type == "CAPITALIZE_NAME":
                conn.execute(text("UPDATE customers SET name = :val WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})

            # 2. REGEX GRADER (Dynamic Scoring)
            result = conn.execute(text("SELECT email, phone, name FROM customers WHERE id = :id"), 
                                 {"id": action.record_id}).fetchone()
            
            if result:
                email_val, phone_val, name_val = result
                
                if action.action_type == "FIX_EMAIL":
                    # Check if the new email matches the standard pattern
                    if re.match(self.email_pattern, email_val):
                        reward = 0.3
                    else:
                        reward = -0.1 # AI failed to fix it properly

                elif action.action_type == "FORMAT_PHONE":
                    # Check if phone starts with + and is digits
                    if re.match(self.phone_pattern, phone_val):
                        reward = 0.3
                    else:
                        reward = -0.1

                elif action.action_type == "CAPITALIZE_NAME":
                    # Check if name is Title Case and trimmed
                    if name_val == name_val.title().strip() and len(name_val) > 0:
                        reward = 0.2
                    else:
                        reward = -0.1
            else:
                reward = -0.5 # Penalty for non-existent ID

            # 3. Check Progress
            dirty_count = conn.execute(text("SELECT COUNT(*) FROM customers WHERE status = 'dirty'")).scalar()
            
        done = (dirty_count == 0) or (self.current_step >= self.max_steps)
        obs = self.get_observation(f"Action {action.action_type} evaluated via Regex.")
        return obs, reward, done

    def get_observation(self, message: str) -> CRMObservation:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM customers")).fetchall()
            dirty_count = conn.execute(text("SELECT COUNT(*) FROM customers WHERE status = 'dirty'")).scalar()
        
        # Focus on the next 'dirty' record
        current_rec = None
        for r in rows:
            if r[4] == 'dirty':
                current_rec = {"id": r[0], "name": r[1], "email": r[2], "phone": r[3]}
                break

        return CRMObservation(
            last_action_status=message,
            current_record=current_rec,
            records_remaining=int(dirty_count),
            logs=f"Step {self.current_step} | {dirty_count} records left."
        )