from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class ActionType(str, Enum):
    """Enumeration of allowed actions to ensure AI consistency."""
    FIX_EMAIL = "FIX_EMAIL"
    FORMAT_PHONE = "FORMAT_PHONE"
    CAPITALIZE_NAME = "CAPITALIZE_NAME"
    DELETE_DUPLICATE = "DELETE_DUPLICATE"

class CRMAction(BaseModel):
    """The action the AI agent takes to clean a record."""
    record_id: int = Field(..., description="The ID of the customer record to modify")
    action_type: ActionType = Field(..., description="The specific cleaning action to perform")
    new_value: Optional[str] = Field(None, description="The corrected string value to insert")

class CRMObservation(BaseModel):
    """What the AI agent sees after taking an action."""
    last_action_status: str = Field(..., description="Success or Error message from last step")
    current_record: Optional[Dict[str, Any]] = Field(None, description="The data of the record just modified")
    records_remaining: int = Field(..., description="How many 'dirty' records are left in the DB")
    logs: str = Field(..., description="Real-time system logs of the operation")

class CRMReward(BaseModel):
    """The numerical feedback for the agent."""
    reward: float = Field(..., description="Value between -1.0 and 1.0")
    done: bool = Field(..., description="Whether the specific task is finished")