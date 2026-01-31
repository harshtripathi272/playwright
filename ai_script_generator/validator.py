"""
Script Validator - Pre-execution validation
Checks syntax and common Playwright patterns before execution
"""
import ast
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """Result of script validation"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    
    def __bool__(self):
        return self.is_valid


class ScriptValidator:
    """Validates generated Playwright scripts before execution"""
    
    # Common Playwright patterns that should be present
    REQUIRED_PATTERNS = [
        (r'async\s+def', "Script should use async functions"),
        (r'playwright', "Script should import/use playwright"),
    ]
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        (r'os\.system\s*\(', "os.system calls are not allowed"),
        (r'subprocess\.(run|Popen|call)', "subprocess calls are not allowed"),
        (r'exec\s*\(', "exec() is not allowed"),
        (r'eval\s*\(', "eval() is not allowed"),
        (r'__import__\s*\(', "Dynamic imports are not allowed"),
        (r'open\s*\([^)]*["\']w', "File writing is not allowed"),
    ]
    
    # Common mistakes in Playwright scripts
    PLAYWRIGHT_WARNINGS = [
        (r'\.click\(\)\s*$', "Consider using click() with a selector or locator"),
        (r'time\.sleep', "Prefer page.wait_for_* methods over time.sleep"),
        (r'\.goto\([^)]+\)\s*(?!.*await)', "goto() should be awaited"),
    ]
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate a script for syntax and safety
        
        Args:
            code: Python code string to validate
            
        Returns:
            ValidationResult with status and any issues found
        """
        errors = []
        warnings = []
        
        # Check syntax
        syntax_error = self._check_syntax(code)
        if syntax_error:
            errors.append(f"Syntax error: {syntax_error}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Check for blocked patterns
        for pattern, message in self.BLOCKED_PATTERNS:
            if re.search(pattern, code):
                errors.append(f"Security: {message}")
        
        # Check for required patterns
        for pattern, message in self.REQUIRED_PATTERNS:
            if not re.search(pattern, code, re.IGNORECASE):
                warnings.append(f"Missing: {message}")
        
        # Check for common mistakes
        for pattern, message in self.PLAYWRIGHT_WARNINGS:
            if re.search(pattern, code):
                warnings.append(f"Warning: {message}")
        
        # Check for proper async/await usage
        await_issues = self._check_async_await(code)
        warnings.extend(await_issues)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
    
    def _check_syntax(self, code: str) -> Optional[str]:
        """Check Python syntax validity"""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"
    
    def _check_async_await(self, code: str) -> list[str]:
        """Check for common async/await issues"""
        issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues
        
        for node in ast.walk(tree):
            # Check for async functions without await
            if isinstance(node, ast.AsyncFunctionDef):
                has_await = any(
                    isinstance(child, ast.Await) 
                    for child in ast.walk(node)
                )
                if not has_await:
                    issues.append(
                        f"Async function '{node.name}' has no await expressions"
                    )
        
        return issues
    
    def extract_main_function(self, code: str) -> Optional[str]:
        """Extract the main entry point function name"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                if node.name in ['main', 'run', 'execute']:
                    return node.name
        
        # Return first async function if no standard name found
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                return node.name
        
        return None
