"""
Context Manager - Maintains session state between retry attempts
Tracks progress, captures failure context, and provides rich error information
"""
import os
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

from config import SCREENSHOTS_DIR


@dataclass
class StepProgress:
    """Tracks a single step's execution"""
    step_number: int
    description: str
    status: str = "pending"  # pending, running, success, failed
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ExecutionContext:
    """Full context of an execution attempt"""
    attempt_number: int
    script_code: str
    steps: list[StepProgress] = field(default_factory=list)
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    console_logs: list[str] = field(default_factory=list)
    network_errors: list[str] = field(default_factory=list)
    final_screenshot: Optional[str] = None
    error_message: Optional[str] = None
    success: bool = False
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ContextManager:
    """Manages execution context across retry attempts"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.attempts: list[ExecutionContext] = []
        self.current_attempt: Optional[ExecutionContext] = None
        
    def start_attempt(self, attempt_number: int, script_code: str) -> ExecutionContext:
        """Start tracking a new execution attempt"""
        self.current_attempt = ExecutionContext(
            attempt_number=attempt_number,
            script_code=script_code,
            start_time=datetime.now().isoformat()
        )
        self.attempts.append(self.current_attempt)
        return self.current_attempt
    
    def add_step(self, step_number: int, description: str) -> StepProgress:
        """Add a new step to track"""
        if not self.current_attempt:
            raise RuntimeError("No active attempt - call start_attempt first")
        
        step = StepProgress(
            step_number=step_number,
            description=description,
            status="pending"
        )
        self.current_attempt.steps.append(step)
        return step
    
    def update_step(self, step_number: int, status: str, 
                    error: Optional[str] = None, 
                    screenshot_path: Optional[str] = None):
        """Update a step's status"""
        if not self.current_attempt:
            return
        
        for step in self.current_attempt.steps:
            if step.step_number == step_number:
                step.status = status
                step.error = error
                step.screenshot_path = screenshot_path
                step.timestamp = datetime.now().isoformat()
                break
    
    def add_console_log(self, message: str):
        """Add a console log entry"""
        if self.current_attempt:
            self.current_attempt.console_logs.append(message)
    
    def add_network_error(self, error: str):
        """Add a network error entry"""
        if self.current_attempt:
            self.current_attempt.network_errors.append(error)
    
    def update_page_state(self, url: str, title: str):
        """Update current page state"""
        if self.current_attempt:
            self.current_attempt.current_url = url
            self.current_attempt.page_title = title
    
    def finish_attempt(self, success: bool, error_message: Optional[str] = None,
                       final_screenshot: Optional[str] = None):
        """Mark the current attempt as finished"""
        if self.current_attempt:
            self.current_attempt.success = success
            self.current_attempt.error_message = error_message
            self.current_attempt.final_screenshot = final_screenshot
            self.current_attempt.end_time = datetime.now().isoformat()
    
    def get_retry_context(self) -> dict:
        """Get context to send to LLM for retry"""
        if not self.attempts:
            return {}
        
        last_attempt = self.attempts[-1]
        
        # Find which step failed
        failed_step = None
        completed_steps = []
        for step in last_attempt.steps:
            if step.status == "failed":
                failed_step = step
            elif step.status == "success":
                completed_steps.append(step.description)
        
        return {
            "attempt_number": last_attempt.attempt_number,
            "error_message": last_attempt.error_message,
            "failed_step": asdict(failed_step) if failed_step else None,
            "completed_steps": completed_steps,
            "current_url": last_attempt.current_url,
            "page_title": last_attempt.page_title,
            "console_logs": last_attempt.console_logs[-10:],  # Last 10 logs
            "network_errors": last_attempt.network_errors[-5:],  # Last 5 errors
            "previous_script": last_attempt.script_code
        }
    
    def save_to_file(self, output_dir: Optional[str] = None):
        """Save full context to JSON file"""
        output_dir = output_dir or SCREENSHOTS_DIR
        filepath = Path(output_dir) / f"context_{self.task_id}.json"
        
        data = {
            "task_id": self.task_id,
            "total_attempts": len(self.attempts),
            "final_success": self.attempts[-1].success if self.attempts else False,
            "attempts": [asdict(a) for a in self.attempts]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(filepath)
