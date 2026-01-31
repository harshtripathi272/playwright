"""
AI Script Generator - Main Entry Point
Orchestrates the full flow: input → generation → validation → execution → retry
"""
import argparse
import asyncio
import uuid
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import MAX_RETRIES, RETRY_DELAY_SECONDS, OUTPUT_DIR
from input_processor import InputProcessor
from agent import PlaywrightAgent
from validator import ScriptValidator
from executor import ScriptExecutor
from context_manager import ContextManager


class AIScriptGenerator:
    """Main orchestrator for AI-powered Playwright script generation"""
    
    def __init__(self):
        self.input_processor = InputProcessor()
        self.agent = PlaywrightAgent()
        self.validator = ScriptValidator()
        self.executor = ScriptExecutor()
    
    async def run(self, input_data: str, input_type: str = "auto") -> dict:
        """
        Run the full generation and execution pipeline
        
        Args:
            input_data: Text description or path to image/video
            input_type: "text", "image", "video", or "auto"
            
        Returns:
            dict with 'success', 'result', 'attempts', and 'script'
        """
        task_id = str(uuid.uuid4())[:8]
        context_manager = ContextManager(task_id)
        
        print(f"\n{'='*60}")
        print(f"🚀 AI Script Generator - Task ID: {task_id}")
        print(f"{'='*60}\n")
        
        # Process input
        print(f"📥 Processing input ({input_type})...")
        try:
            processed_input = self.input_processor.process(input_data, input_type)
            print(f"   ✓ Input processed as: {processed_input['type']}")
        except Exception as e:
            print(f"   ✗ Failed to process input: {e}")
            return {"success": False, "error": str(e), "attempts": 0}
        
        # Retry loop
        last_result = None
        generated_script = None
        
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n{'─'*40}")
            print(f"🔄 Attempt {attempt}/{MAX_RETRIES}")
            print(f"{'─'*40}")
            
            # Get retry context if not first attempt
            retry_context = None
            if attempt > 1:
                retry_context = context_manager.get_retry_context()
                print(f"   📋 Using context from previous failure")
            
            # Start tracking this attempt
            context_manager.start_attempt(attempt, "")
            
            # Generate script
            print(f"\n🤖 Generating Playwright script...")
            try:
                generation_result = self.agent.generate_script(processed_input, retry_context)
                generated_script = generation_result["script"]
                steps = generation_result.get("steps", [])
                
                print(f"   ✓ Generated script with {len(steps)} steps:")
                for i, step in enumerate(steps, 1):
                    print(f"      {i}. {step}")
                    context_manager.add_step(i, step)
                
            except Exception as e:
                print(f"   ✗ Generation failed: {e}")
                context_manager.finish_attempt(False, str(e))
                
                if attempt < MAX_RETRIES:
                    print(f"   ⏳ Retrying in {RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                continue
            
            # Update context with generated script
            context_manager.current_attempt.script_code = generated_script
            
            # Validate script
            print(f"\n✅ Validating script...")
            validation = self.validator.validate(generated_script)
            
            if not validation.is_valid:
                print(f"   ✗ Validation failed:")
                for error in validation.errors:
                    print(f"      - {error}")
                
                context_manager.finish_attempt(False, f"Validation: {'; '.join(validation.errors)}")
                
                if attempt < MAX_RETRIES:
                    print(f"   ⏳ Retrying in {RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                continue
            
            if validation.warnings:
                print(f"   ⚠ Warnings:")
                for warning in validation.warnings:
                    print(f"      - {warning}")
            
            print(f"   ✓ Validation passed")
            
            # Execute script
            print(f"\n⚡ Executing script...")
            try:
                result = await self.executor.execute(generated_script, task_id)
                last_result = result
                
                if result.success:
                    print(f"   ✓ Execution successful! ({result.execution_time_seconds:.1f}s)")
                    if result.screenshot_path:
                        print(f"   📸 Screenshot: {result.screenshot_path}")
                    
                    context_manager.finish_attempt(True, final_screenshot=result.screenshot_path)
                    
                    # Save script to file
                    script_path = Path(OUTPUT_DIR) / f"script_{task_id}.py"
                    with open(script_path, 'w') as f:
                        f.write(generated_script)
                    print(f"   💾 Script saved: {script_path}")
                    
                    # Save context
                    context_file = context_manager.save_to_file()
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "script_path": str(script_path),
                        "screenshot_path": result.screenshot_path,
                        "attempts": attempt,
                        "script": generated_script
                    }
                
                else:
                    print(f"   ✗ Execution failed: {result.error}")
                    print(f"   Output:\n{result.output[:500]}")
                    
                    context_manager.update_page_state(
                        result.current_url or "unknown",
                        result.page_title or "unknown"
                    )
                    context_manager.finish_attempt(
                        False, 
                        result.error,
                        final_screenshot=result.screenshot_path
                    )
                    
            except Exception as e:
                print(f"   ✗ Execution error: {e}")
                context_manager.finish_attempt(False, str(e))
                last_result = None
            
            if attempt < MAX_RETRIES:
                print(f"\n   ⏳ Retrying in {RETRY_DELAY_SECONDS}s...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        
        # All retries exhausted
        print(f"\n{'='*60}")
        print(f"❌ All {MAX_RETRIES} attempts failed")
        print(f"{'='*60}")
        
        # Save context for debugging
        context_file = context_manager.save_to_file()
        print(f"📋 Debug context saved: {context_file}")
        
        return {
            "success": False,
            "task_id": task_id,
            "attempts": MAX_RETRIES,
            "last_error": last_result.error if last_result else "Generation failed",
            "context_file": context_file,
            "script": generated_script
        }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI-powered Playwright script generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Static script generation (default)
  python main.py --text "Go to google.com and search for weather"
  
  # Dynamic agent (thinks step-by-step based on live page)
  python main.py --text "Go to BookMyShow and search Border 2" --dynamic
  
  # Image input
  python main.py --image screenshot.png
  
  # Video input
  python main.py --video recording.mp4
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", "-t", help="Text description of automation task")
    group.add_argument("--image", "-i", help="Path to image file")
    group.add_argument("--video", "-v", help="Path to video file")
    
    parser.add_argument("--dynamic", "-d", action="store_true",
                        help="Use dynamic agent (thinks step-by-step based on live page)")
    parser.add_argument("--url", "-u", help="Starting URL (optional, for dynamic mode)")
    
    args = parser.parse_args()
    
    # Dynamic mode - use think-act loop agent
    if args.dynamic and args.text:
        from dynamic_agent import DynamicAgent
        
        agent = DynamicAgent()
        result = agent.run(args.text, args.url)
        
        print(f"\n{'='*60}")
        if result["success"]:
            print("✅ SUCCESS!")
            print(f"   Steps: {len(result['steps'])}")
            print(f"   Final URL: {result.get('final_url')}")
        else:
            print("❌ FAILED")
            print(f"   Error: {result.get('error')}")
            print(f"   Steps completed: {len(result['steps'])}")
        print(f"{'='*60}\n")
        
        return 0 if result["success"] else 1
    
    # Static mode - generate full script upfront
    # Determine input type and data
    if args.text:
        input_data = args.text
        input_type = "text"
    elif args.image:
        input_data = args.image
        input_type = "image"
    else:
        input_data = args.video
        input_type = "video"
    
    # Run the generator
    generator = AIScriptGenerator()
    result = asyncio.run(generator.run(input_data, input_type))
    
    # Print final result
    print(f"\n{'='*60}")
    if result["success"]:
        print("✅ SUCCESS!")
        print(f"   Script: {result.get('script_path')}")
        print(f"   Attempts: {result['attempts']}")
    else:
        print("❌ FAILED")
        print(f"   Error: {result.get('last_error')}")
        print(f"   Attempts: {result['attempts']}")
    print(f"{'='*60}\n")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
