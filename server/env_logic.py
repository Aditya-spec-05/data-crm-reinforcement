import os
import re
from sqlalchemy import create_engine, text
from typing import Tuple, Dict, Any
from .models import CRMAction, CRMObservation

class CRMEnvLogic:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///crm.db")
        self.engine = create_engine(self.db_url)
        self.max_steps = 20
        self.current_step = 0
        self.current_task = "task_easy_email"
        
        # Regex Patterns for validation
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.phone_pattern = r'^\+\d{7,15}$'

    def reset_db(self, task_id: str = "task_easy_email"):
        self.current_step = 0
        self.current_task = task_id
        
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
            
            # Scenario data changes based on task_id to satisfy "3 tasks" requirement
            if task_id == "task_medium_phone":
                data = [
                    {"id": 1, "name": 'Aditya', "email": 'aditya@gmail.com', "phone": '12345', "status": 'dirty'},
                    {"id": 2, "name": 'John Doe', "email": 'john.doe@gmail.com', "phone": '9876543210', "status": 'dirty'}
                ]
            elif task_id == "task_hard_crm":
                data = [
                    {"id": 1, "name": 'aditya', "email": 'aditya[at]gmail.com', "phone": '12345', "status": 'dirty'},
                    {"id": 2, "name": 'john', "email": 'john@gmail.com', "phone": '+1234567', "status": 'dirty'}
                ]
            else: # default: task_easy_email
                data = [
                    {"id": 1, "name": 'Aditya', "email": 'aditya[at]gmail.com', "phone": '+123456789', "status": 'dirty'},
                    {"id": 2, "name": 'John', "email": 'john.doe#gmail.com', "phone": '+987654321', "status": 'dirty'}
                ]
            
            for row in data:
                conn.execute(text("INSERT INTO customers (id, name, email, phone, status) VALUES (:id, :name, :email, :phone, :status)"), row)
        
        return self.get_observation("Task started: " + task_id)

    def step(self, action: CRMAction) -> Tuple[CRMObservation, float, bool]:
        self.current_step += 1
        # START WITH SMALL NON-ZERO REWARD (Compliance)
        reward = 0.05 
        
        with self.engine.begin() as conn:
            # 1. Update the Database
            if action.action_type == "FIX_EMAIL":
                conn.execute(text("UPDATE customers SET email = :val, status = 'cleaned' WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})
            elif action.action_type == "FORMAT_PHONE":
                conn.execute(text("UPDATE customers SET phone = :val, status = 'cleaned' WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})
            elif action.action_type == "CAPITALIZE_NAME":
                conn.execute(text("UPDATE customers SET name = :val, status = 'cleaned' WHERE id = :id"), 
                             {"val": action.new_value, "id": action.record_id})

            # 2. REGEX GRADER (Dynamic Scoring strictly between 0 and 1)
            result = conn.execute(text("SELECT email, phone, name FROM customers WHERE id = :id"), 
                                     {"id": action.record_id}).fetchone()
            
            if result:
                email_val, phone_val, name_val = result
                
                if action.action_type == "FIX_EMAIL":
                    if re.match(self.email_pattern, email_val):
                        reward = 0.85 # Success (not 1.0)
                    else:
                        reward = 0.15 # Fail (not 0.0)

                elif action.action_type == "FORMAT_PHONE":
                    if re.match(self.phone_pattern, phone_val):
                        reward = 0.85
                    else:
                        reward = 0.15

                elif action.action_type == "CAPITALIZE_NAME":
                    if name_val == name_val.title().strip() and len(name_val) > 0:
                        reward = 0.75
                    else:
                        reward = 0.15
            else:
                reward = 0.05 # Penalty for bad ID (not 0.0)

            # 3. Check Progress
            dirty_count = conn.execute(text("SELECT COUNT(*) FROM customers WHERE status = 'dirty'")).scalar()
            
        done = (dirty_count == 0) or (self.current_step >= self.max_steps)
        obs = self.get_observation(f"Action {action.action_type} evaluated.")
        return obs, reward, done

    def get_observation(self, message: str) -> CRMObservation:
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM customers")).fetchall()
            dirty_count = conn.execute(text("SELECT COUNT(*) FROM customers WHERE status = 'dirty'")).scalar()
        
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
