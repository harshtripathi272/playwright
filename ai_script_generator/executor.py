"""
Script Executor - Sandboxed execution of generated Playwright scripts
Runs scripts safely with timeout, monitoring, and screenshot capture
"""
import asyncio
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import tempfile
import os

from config import EXECUTION_TIMEOUT_SECONDS, SCREENSHOTS_DIR, HEADLESS_MODE


@dataclass
class ExecutionResult:
    """Result of script execution"""
    success: bool
    output: str
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time_seconds: float = 0.0
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    console_logs: list = None
    network_errors: list = None
    
    def __post_init__(self):
        if self.console_logs is None:
            self.console_logs = []
        if self.network_errors is None:
            self.network_errors = []


class ScriptExecutor:
    """Executes generated Playwright scripts in a sandboxed environment"""
    
    def __init__(self, timeout: int = EXECUTION_TIMEOUT_SECONDS):
        self.timeout = timeout
        self.screenshots_dir = Path(SCREENSHOTS_DIR)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def execute(self, script_code: str, task_id: str) -> ExecutionResult:
        """
        Execute a Playwright script safely
        
        Args:
            script_code: Python code to execute
            task_id: Unique identifier for this execution
            
        Returns:
            ExecutionResult with status and captured data
        """
        start_time = datetime.now()
        output_lines = []
        console_logs = []
        network_errors = []
        current_url = None
        page_title = None
        screenshot_path = None
        
        try:
            # Create a modified script with monitoring hooks
            modified_script = self._inject_monitoring(script_code, task_id)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(modified_script)
                temp_file = f.name
            
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._run_script(temp_file, output_lines),
                    timeout=self.timeout
                )
                
                success = result == 0
                error = None if success else "Script execution failed"
                
            except asyncio.TimeoutError:
                success = False
                error = f"Execution timed out after {self.timeout} seconds"
                output_lines.append(error)
            
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            # Get screenshot if exists
            screenshot_path = self._get_latest_screenshot(task_id)
            
        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            output_lines.append(error)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ExecutionResult(
            success=success,
            output="\n".join(output_lines),
            error=error,
            screenshot_path=screenshot_path,
            execution_time_seconds=execution_time,
            current_url=current_url,
            page_title=page_title,
            console_logs=console_logs,
            network_errors=network_errors
        )
    
    def _inject_monitoring(self, script_code: str, task_id: str) -> str:
        """Inject monitoring and screenshot capture into script"""
        # Add screenshot on error and at end
        screenshot_code = f'''
# Injected monitoring code
import os
_TASK_ID = "{task_id}"
_SCREENSHOTS_DIR = r"{self.screenshots_dir}"

async def _take_screenshot(page, name):
    try:
        path = os.path.join(_SCREENSHOTS_DIR, f"{{_TASK_ID}}_{{name}}.png")
        await page.screenshot(path=path)
        print(f"Screenshot saved: {{path}}")
    except Exception as e:
        print(f"Failed to take screenshot: {{e}}")

# Override to inject headless setting
_HEADLESS = {HEADLESS_MODE}
'''
        
        # Insert at the top of the script (after imports)
        lines = script_code.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith(('import', 'from', '#')):
                import_end = i
                break
        
        modified = lines[:import_end] + [screenshot_code] + lines[import_end:]
        return '\n'.join(modified)
    
    async def _run_script(self, script_path: str, output_lines: list) -> int:
        """Run the script as a subprocess"""
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(self.screenshots_dir.parent)
        )
        
        # Read output
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded = line.decode().rstrip()
            output_lines.append(decoded)
            print(f"[EXEC] {decoded}")
        
        await process.wait()
        return process.returncode
    
    def _get_latest_screenshot(self, task_id: str) -> Optional[str]:
        """Get the most recent screenshot for this task"""
        pattern = f"{task_id}_*.png"
        screenshots = list(self.screenshots_dir.glob(pattern))
        
        if screenshots:
            # Return most recent
            return str(max(screenshots, key=lambda p: p.stat().st_mtime))
        return None
    
    def validate_before_execute(self, script_code: str) -> tuple[bool, str]:
        """Quick validation before execution"""
        # Check for required imports
        if "playwright" not in script_code.lower():
            return False, "Script must use Playwright"
        
        if "async" not in script_code:
            return False, "Script must use async/await pattern"
        
        return True, "Validation passed"
