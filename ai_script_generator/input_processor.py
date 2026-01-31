"""
Input Processor - Handles text, image, and video inputs
Converts multimodal inputs into structured prompts for the LLM
"""
import base64
from pathlib import Path
from typing import Union
from PIL import Image
import io


class InputProcessor:
    """Processes different input types into LLM-ready prompts"""
    
    def __init__(self):
        self.supported_image_formats = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.webm']
    
    def process(self, input_data: Union[str, Path], input_type: str = "auto") -> dict:
        """
        Process input and return structured data for LLM
        
        Args:
            input_data: Text string or path to file
            input_type: "text", "image", "video", or "auto" (detect automatically)
            
        Returns:
            dict with 'type', 'content', and 'prompt' keys
        """
        if input_type == "auto":
            input_type = self._detect_type(input_data)
        
        if input_type == "text":
            return self._process_text(input_data)
        elif input_type == "image":
            return self._process_image(input_data)
        elif input_type == "video":
            return self._process_video(input_data)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
    
    def _detect_type(self, input_data: Union[str, Path]) -> str:
        """Auto-detect input type based on content or file extension"""
        if isinstance(input_data, Path) or (isinstance(input_data, str) and Path(input_data).exists()):
            path = Path(input_data)
            suffix = path.suffix.lower()
            
            if suffix in self.supported_image_formats:
                return "image"
            elif suffix in self.supported_video_formats:
                return "video"
        
        return "text"
    
    def _process_text(self, text: str) -> dict:
        """Process text input"""
        return {
            "type": "text",
            "content": text,
            "prompt": self._create_text_prompt(text)
        }
    
    def _process_image(self, image_path: Union[str, Path]) -> dict:
        """Process image input - encode for vision model"""
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read and encode image
        with open(path, "rb") as f:
            image_data = f.read()
        
        base64_image = base64.b64encode(image_data).decode("utf-8")
        
        # Get image dimensions for context
        img = Image.open(path)
        width, height = img.size
        
        return {
            "type": "image",
            "content": base64_image,
            "mime_type": self._get_mime_type(path),
            "dimensions": {"width": width, "height": height},
            "prompt": self._create_image_prompt()
        }
    
    def _process_video(self, video_path: Union[str, Path]) -> dict:
        """Process video input - extract key frames"""
        path = Path(video_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        try:
            import cv2
        except ImportError:
            raise ImportError("opencv-python required for video processing")
        
        frames = self._extract_key_frames(path)
        
        return {
            "type": "video",
            "content": frames,  # List of base64 encoded frames
            "frame_count": len(frames),
            "prompt": self._create_video_prompt()
        }
    
    def _extract_key_frames(self, video_path: Path, max_frames: int = 5) -> list:
        """Extract key frames from video for analysis"""
        import cv2
        
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            raise ValueError("Could not read video frames")
        
        # Sample frames evenly across video
        frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
        frames = []
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if ret:
                # Convert to base64
                _, buffer = cv2.imencode('.jpg', frame)
                base64_frame = base64.b64encode(buffer).decode('utf-8')
                frames.append(base64_frame)
        
        cap.release()
        return frames
    
    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type from file extension"""
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(path.suffix.lower(), 'image/png')
    
    def _create_text_prompt(self, task_description: str) -> str:
        """Create prompt for text-based task"""
        return f"""You are a Playwright automation expert. Based on the following task description, 
generate a complete Python script using Playwright to accomplish this task.

TASK: {task_description}

Generate a script that:
1. Uses async Playwright with proper browser/context/page management
2. Includes proper error handling
3. Takes screenshots at key steps
4. Uses explicit waits instead of arbitrary delays
"""
    
    def _create_image_prompt(self) -> str:
        """Create prompt for image-based task"""
        return """You are a Playwright automation expert. Analyze this image of a web interface 
and generate a Python script to automate the actions shown or implied.

Look for:
1. URLs or navigation targets
2. Form fields and input areas
3. Buttons or clickable elements
4. Any annotations or arrows indicating actions

Generate a complete async Playwright script to accomplish what the image shows.
"""
    
    def _create_video_prompt(self) -> str:
        """Create prompt for video-based task"""
        return """You are a Playwright automation expert. These frames are from a video showing 
a web automation workflow. Analyze the sequence and generate a Python script that 
replicates this workflow.

Identify:
1. The sequence of pages/screens
2. User interactions (clicks, typing, scrolling)
3. Navigation flow
4. Expected outcomes at each step

Generate a complete async Playwright script to replicate this workflow.
"""
