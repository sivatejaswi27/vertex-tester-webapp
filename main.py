"""
Vertex Tester - Multi-Language Web Application Module

Adapted from multi-language main.py for Streamlit web application.
Supports Python and Java with automatic language detection.

Authors: Dhulipala Siva Tejaswi, Kaushal Girish & Monish Anand
Version: 2.0.0 (Multi-Language Web Version)
Date: 2025-01-30
"""

import ast
import os
import json
import tempfile
import shutil
import tiktoken
from google import genai
from google.genai import types
from google.cloud import aiplatform

def init_vertex_ai():
    project = "ascendant-lore-466708-p3"
    location = "us-central1"
    if project and location:
        aiplatform.init(project=project, location=location)
    else:
        aiplatform.init()

init_vertex_ai()

# Handle javalang import gracefully
try:
    import javalang
except ImportError:
    javalang = None

class WebUnittester:
    """
    Multi-language AI-powered unit test generator for web applications.
    
    Supports Python and Java with automatic language detection and
    language-specific test framework generation.
    """
    
    @staticmethod
    def process_uploaded_file(uploaded_file, api_key):
        """
        Process uploaded file with automatic language detection.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            api_key: Google Cloud API key
            
        Returns:
            tuple: (test_file_content, test_file_name, detected_language) or (None, None, None) if failed
        """
        
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        upload_dir = os.path.join(temp_dir, 'uploads')
        output_dir = os.path.join(temp_dir, 'outputs')
        
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Save uploaded file
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Detect language
            language = WebUnittester.detect_language(file_path)
            print(f"Detected language: {language}")
            
            # Process file using adapted mainProcessor
            test_file_path = WebUnittester.mainProcessor(file_path, output_dir, api_key)
            
            if test_file_path and os.path.exists(test_file_path):
                # Read test file content
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    test_content = f.read()
                
                test_filename = os.path.basename(test_file_path)
                return test_content, test_filename, language
            else:
                return None, None, language
                
        except Exception as e:
            # Try to detect language for error reporting
            try:
                language = WebUnittester.detect_language(os.path.join(upload_dir, uploaded_file.name))
            except:
                language = "unknown"
            raise Exception(f"Error processing {uploaded_file.name}: {str(e)}")
        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def detect_language(file_path):
        """
        Detect programming language based on file extension.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            str: Detected language ('python' or 'java')
            
        Raises:
            ValueError: If file extension is not supported
        """
        _, ext = os.path.splitext(file_path.lower())
        if ext == '.py':
            return 'python'
        elif ext == '.java':
            return 'java'
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .py, .java")
    
    @staticmethod
    def parse_python_file(src, file_path):
        """
        Parse Python file using AST and extract function/method information.
        
        Args:
            src: Source code content
            file_path: Path to the source file
            
        Returns:
            list: Function metadata dictionaries
            
        Raises:
            ValueError: If Python syntax errors are encountered
        """
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            raise ValueError(f"SyntaxError while parsing Python: {e}")

        parent_map = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[child] = parent

        idx = 0
        blocks = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name

                # Determine nearest class context, if any
                class_ctx = None
                cur = node
                while cur in parent_map:
                    cur = parent_map[cur]
                    if isinstance(cur, ast.ClassDef):
                        class_ctx = cur.name
                        break

                # Get exact source segment for this function
                code_segment = ast.get_source_segment(src, node)
                if code_segment is None:
                    start = getattr(node, 'lineno', None)
                    end = getattr(node, 'end_lineno', None) or (start or 0)
                    code_segment = "\n".join(src.splitlines()[start-1:end])

                # Extract signature line
                signature_line = ""
                for line in code_segment.splitlines():
                    if line.strip().startswith("def ") or line.strip().startswith("async def "):
                        signature_line = line.strip()
                        break

                start_line = getattr(node, 'lineno', None)
                end_line = getattr(node, 'end_lineno', None)

                block = {
                    "block_id": f"{os.path.basename(file_path)}_{idx}",
                    "function_name": name,
                    "class_context": class_ctx,
                    "start_line": start_line,
                    "end_line": end_line,
                    "signature": signature_line,
                    "code": code_segment,
                    "language": "python"
                }
                blocks.append(block)
                idx += 1

        return blocks

    @staticmethod
    def parse_java_file(src, file_path):
        """
        Parse Java file using javalang and extract method/constructor information.
        
        Args:
            src: Source code content
            file_path: Path to the source file
            
        Returns:
            list: Method/constructor metadata dictionaries
            
        Raises:
            ImportError: If javalang library is not available
            ValueError: If Java parsing errors are encountered
        """
        if javalang is None:
            raise ImportError("javalang library is required for Java parsing. Please install: pip install javalang")

        try:
            tree = javalang.parse.parse(src)
        except Exception as e:
            raise ValueError(f"Error parsing Java file: {e}")

        blocks = []
        idx = 0
        lines = src.splitlines()

        # Extract package name
        package_name = tree.package.name if tree.package else None

        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = node.name
           
            # Get all methods in this class
            for method_path, method_node in node.filter(javalang.tree.MethodDeclaration):
                method_name = method_node.name
               
                # Extract method signature
                params = []
                if method_node.parameters:
                    for param in method_node.parameters:
                        param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                        params.append(f"{param_type} {param.name}")
               
                return_type = method_node.return_type.name if method_node.return_type and hasattr(method_node.return_type, 'name') else 'void'
                signature = f"public {return_type} {method_name}({', '.join(params)})"
               
                # Get method source code (approximate)
                start_line = method_node.position.line if method_node.position else None
                end_line = start_line
               
                # Try to find method end (basic heuristic)
                if start_line:
                    brace_count = 0
                    method_started = False
                    method_lines = []
                   
                    for i, line in enumerate(lines[start_line-1:], start_line):
                        method_lines.append(line)
                        if '{' in line:
                            brace_count += line.count('{')
                            method_started = True
                        if '}' in line:
                            brace_count -= line.count('}')
                       
                        if method_started and brace_count == 0:
                            end_line = i
                            break
                   
                    code_segment = '\n'.join(method_lines)
                else:
                    code_segment = f"// Method {method_name} - source extraction failed"

                block = {
                    "block_id": f"{os.path.basename(file_path)}_{idx}",
                    "function_name": method_name,
                    "class_context": class_name,
                    "package_context": package_name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "signature": signature,
                    "code": code_segment,
                    "language": "java"
                }
                blocks.append(block)
                idx += 1

            # Also get constructors
            for constructor_path, constructor_node in node.filter(javalang.tree.ConstructorDeclaration):
                constructor_name = constructor_node.name
               
                # Extract constructor signature
                params = []
                if constructor_node.parameters:
                    for param in constructor_node.parameters:
                        param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                        params.append(f"{param_type} {param.name}")
               
                signature = f"public {constructor_name}({', '.join(params)})"
               
                # Get constructor source code (approximate)
                start_line = constructor_node.position.line if constructor_node.position else None
                end_line = start_line
               
                if start_line:
                    brace_count = 0
                    constructor_started = False
                    constructor_lines = []
                   
                    for i, line in enumerate(lines[start_line-1:], start_line):
                        constructor_lines.append(line)
                        if '{' in line:
                            brace_count += line.count('{')
                            constructor_started = True
                        if '}' in line:
                            brace_count -= line.count('}')
                       
                        if constructor_started and brace_count == 0:
                            end_line = i
                            break
                   
                    code_segment = '\n'.join(constructor_lines)
                else:
                    code_segment = f"// Constructor {constructor_name} - source extraction failed"

                block = {
                    "block_id": f"{os.path.basename(file_path)}_{idx}",
                    "function_name": constructor_name,
                    "class_context": class_name,
                    "package_context": package_name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "signature": signature,
                    "code": code_segment,
                    "language": "java",
                    "is_constructor": True
                }
                blocks.append(block)
                idx += 1

        return blocks
    
    @staticmethod
    def mainProcessor(file_path, out_dir, api_key):
        """
        Main processing method that analyzes code and generates AI-powered tests.
        
        Automatically detects language, parses source code, and generates
        appropriate unit tests using Google Gemini AI.
        
        Returns:
            str: Path to generated test file, or None if failed
        """
        
        # Read and parse the source file
        with open(file_path, 'r', encoding='utf-8') as file:
            src = file.read()
        
        # Detect language
        language = WebUnittester.detect_language(file_path)
        print(f"Detected language: {language}")
        
        # Parse based on language
        if language == 'python':
            blocks = WebUnittester.parse_python_file(src, file_path)
        elif language == 'java':
            blocks = WebUnittester.parse_java_file(src, file_path)
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Save analysis results for debugging
        summary_path = os.path.join(out_dir, "summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(blocks, f, indent=2)

        print(f"Found {len(blocks)} functions/methods to test")
        
        if len(blocks) == 0:
            raise ValueError(f"No functions or methods found in the uploaded {language} file")
        
        # Generate AI-powered tests
        return WebUnittester.generate_tests(blocks, language, out_dir)

    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Count tokens in text for batch processing optimization.
        
        Args:
            text: Text content to analyze
            
        Returns:
            int: Estimated token count
        """
        try:
            enc = tiktoken.encoding_for_model("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return max(1, len(text.split()))

    @staticmethod    
    def batch_blocks_by_tokens(blocks, max_tokens_per_batch: int):
        """
        Group code blocks into batches for efficient API processing.
        
        Args:
            blocks: List of function/method metadata
            max_tokens_per_batch: Maximum tokens allowed per batch
            
        Returns:
            list: List of batched block groups
        """
        if not blocks:
            return []

        batches = []
        current_batch = []
        current_tokens = 0

        for b in blocks:
            block_text = json.dumps(b, ensure_ascii=False)
            t = WebUnittester.count_tokens(block_text)

            if t > max_tokens_per_batch:
                # This single block doesn't fit in the budget.
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                batches.append([b])
                continue

            if current_batch and (current_tokens + t) > max_tokens_per_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(b)
            current_tokens += t

        if current_batch:
            batches.append(current_batch)

        return batches    

    @staticmethod
    def generate_tests(blocks, language, output_dir):
        """
        Generate unit tests using Google Gemini AI with language-specific optimization.
        
        Args:
            blocks: List of function/method metadata dictionaries
            language: Programming language ('python' or 'java')
            output_dir: Directory to save test files
            
        Returns:
            str: Path to generated test file, or None if failed
        """
        
        # Batch processing for large codebases
        per_batch_tokens = 195000
        batches = WebUnittester.batch_blocks_by_tokens(blocks, per_batch_tokens)
        
        print(f"Processing {len(batches)} batch(es)...")
        
        # Determine file extension based on language
        if language == "python":
            ext = "py"
        else:
            ext = "java"    
        
        try:
            # Initialize Gemini client
            client = genai.Client(
                vertexai=True,
                api_key="AQ.Ab8RN6KAMuExsK5BuaC48qHaoWUCn6AB3i7sJwxi4rbT0QjA8w",
            )

            # Dynamic system instructions based on detected language
            if language == "python":
                framework_info = "pytest framework"
                test_imports = "import pytest"
                example_test = """
                # Example for Python:
                import pytest
                from calculator import Calculator
                
                def test_Calculator_divide_normal():
                    calc = Calculator()
                    assert calc.divide(10, 2) == 5
                
                def test_Calculator_divide_zero_raises():
                    calc = Calculator()
                    with pytest.raises(ZeroDivisionError) as excinfo:
                        calc.divide(5, 0)
                    assert "Cannot divide by zero" in str(excinfo.value)
                """
            else:  # Java
                framework_info = "JUnit framework"
                test_imports = "import org.junit.jupiter.api.Test; import static org.junit.jupiter.api.Assertions.*;"
                example_test = """
                # Example for Java:
                import org.junit.jupiter.api.Test;
                import static org.junit.jupiter.api.Assertions.*;
                
                public class CalculatorTest {
                    @Test
                    public void testDivideNormal() {
                        Calculator calc = new Calculator();
                        assertEquals(5.0, calc.divide(10, 2), 0.001);
                    }
                    
                    @Test
                    public void testDivideByZero() {
                        Calculator calc = new Calculator();
                        assertThrows(ArithmeticException.class, () -> {
                            calc.divide(10, 0);
                        });
                    }
                }
                """

            si_text1 = f"""You are an expert {language} test generator. Create comprehensive unit tests using {framework_info}.

            For each function/method, generate:
            1. Normal operation tests with typical inputs
            2. Edge cases and boundary conditions
            3. Error conditions and exception handling
            4. Use proper imports: {test_imports}
            5. Generate clean, readable, well-documented test code

            Language-specific guidelines:
            - For Python: Use pytest framework with assert statements
            - For Java: Use JUnit 5 framework with annotations and assertions
            - Create comprehensive test coverage
            - Handle language-specific features appropriately

            Output only the {language} test file content with proper imports and test structure.
            No explanations or meta-text, just clean test code.

            {example_test}
            """

            model = "gemini-2.5-flash"
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.8,
                max_output_tokens=8192,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    )
                ],
                system_instruction=[types.Part.from_text(text=si_text1)],
            )
            
            # Determine test file name
            if blocks:
                module_name = blocks[0]["block_id"].split("_")[0]
                class_name = None
                for block in blocks:
                    if block.get("class_context"):
                        class_name = block["class_context"]
                        break
                
                # Create test filename
                if class_name:
                    test_filename = f"test_{class_name}.{ext}" if language == "python" else f"{class_name}Test.{ext}"
                else:
                    # Use module name without extension
                    base_module = os.path.splitext(module_name)[0]
                    test_filename = f"test_{base_module}.{ext}" if language == "python" else f"{base_module}Test.{ext}"
            else:
                test_filename = f"test_generated.{ext}" if language == "python" else f"GeneratedTest.{ext}"
            
            test_path = os.path.join(output_dir, test_filename)

            # Process batches with streaming output
            for batch_idx, batch in enumerate(batches):
                print(f"🤖 Processing batch {batch_idx + 1}/{len(batches)}: |", end=" ", flush=True)
                
                contents = [
                    types.Content(
                    role="user",
                    parts=[
                        {
                        "text": json.dumps(batch, indent=2)
                        }
                    ]
                    )
                ]
                
                # Generate tests
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # Open file in append mode for batches after the first
                mode = "w" if batch_idx == 0 else "a"
                
                with open(test_path, mode, encoding='utf-8') as f:
                    if batch_idx > 0:
                        f.write("\n\n")  # Add spacing between batches
                    f.write(response.text)
                    print(" ✅ done!")
            
            print(f"✅ All {language} tests generated successfully: {test_path}")
            return test_path
                
        except Exception as e:
            print(f"❌ Error generating {language} tests: {e}")
            raise Exception(f"Failed to generate {language} tests: {str(e)}")