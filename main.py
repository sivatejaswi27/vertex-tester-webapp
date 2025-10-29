import ast
import os
import json
import tempfile
import shutil
import tiktoken
from google import genai
from google.genai import types
import time
import re



try:
    import javalang
except ImportError:
    javalang = None

class WebUnittester():

    @staticmethod
    def process_uploaded_file(uploaded_file, api_key):
        temp_dir = tempfile.mkdtemp()
        upload_dir = os.path.join(temp_dir, 'uploads')
        output_dir = os.path.join(temp_dir, 'outputs')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        try:
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            language = WebUnittester.detect_language(file_path)
            print(f"Detected language: {language}")
            test_file_path = WebUnittester.mainProcessor(file_path, output_dir, api_key)
            if test_file_path and os.path.exists(test_file_path):
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    test_content = f.read()
                test_filename = os.path.basename(test_file_path)
                return test_content, test_filename, language
            else:
                return None, None, language
        except Exception as e:
            try:
                language = WebUnittester.detect_language(os.path.join(upload_dir, uploaded_file.name))
            except:
                language = "unknown"
            raise Exception(f"Error processing {uploaded_file.name}: {str(e)}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def detect_language(file_path):
        _, ext = os.path.splitext(file_path.lower())
        if ext == '.py':
            return 'python'
        elif ext == '.java':
            return 'java'
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .py, .java")

    @staticmethod
    def parse_python_file(src, file_path):
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
                class_ctx = None
                cur = node
                while cur in parent_map:
                    cur = parent_map[cur]
                    if isinstance(cur, ast.ClassDef):
                        class_ctx = cur.name
                        break
                code_segment = ast.get_source_segment(src, node)
                if code_segment is None:
                    start = getattr(node, 'lineno', None)
                    end = getattr(node, 'end_lineno', None) or (start or 0)
                    code_segment = "\n".join(src.splitlines()[start-1:end])
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
        Falls back to a regex-based parser if javalang fails.
        """
        if javalang is None:
            raise ImportError("javalang library is required for Java parsing. Please install: pip install javalang")

        # Try javalang first
        try:
            tree = javalang.parse.parse(src)
        except Exception as e:
            # Fallback: simple regex-based parser to extract method/constructor stubs
            blocks = []
            idx = 0
            lines = src.splitlines()
            package_name = None
            m = re.search(r"^\s*package\s+([\w\.]+);", src, re.MULTILINE)
            if m:
                package_name = m.group(1)

            # Find class declarations
            for class_match in re.finditer(r"class\s+(\w+)", src):
                class_name = class_match.group(1)
                # crude scan inside class body by brace counting from class start
                start_pos = class_match.end()
                brace_count = 0
                class_body = ''
                for i, ch in enumerate(src[start_pos:], start_pos):
                    class_body += ch
                    if ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        if brace_count == 0:
                            break
                        brace_count -= 1
                # find methods and constructors inside class_body
                for mtd in re.finditer(r"([\w\<\>\[\]]+\s+)?(\w+)\s*\(([^)]*)\)\s*\{", class_body):
                    ret = mtd.group(1) or 'void'
                    name = mtd.group(2)
                    params = mtd.group(3).strip()
                    params_list = []
                    if params:
                        for p in params.split(','):
                            params_list.append(p.strip())
                    signature = f"{ret.strip()} {name}({', '.join(params_list)})"
                    # attempt to grab method source by searching braces from match position
                    method_start = src.find(mtd.group(0), class_match.end())
                    if method_start == -1:
                        code_segment = "// source extraction failed"
                        start_line = None
                        end_line = None
                    else:
                        # find method block via brace counting
                        i = method_start
                        brace = 0
                        method_lines = []
                        started = False
                        for j, ch in enumerate(src[method_start:], method_start):
                            if ch == '{':
                                brace += 1
                                started = True
                            elif ch == '}':
                                brace -= 1
                            method_lines.append(ch)
                            if started and brace == 0:
                                break
                        code_segment = ''.join(method_lines)
                        # compute line numbers
                        start_line = src[:method_start].count('\n') + 1
                        end_line = start_line + code_segment.count('\n')

                    block = {
                        "block_id": f"{os.path.basename(file_path)}_{idx}",
                        "function_name": name,
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
            return blocks

        # If javalang succeeded, continue with original logic
        blocks = []
        idx = 0
        lines = src.splitlines()
        package_name = tree.package.name if tree.package else None

        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = node.name
            for method_path, method_node in node.filter(javalang.tree.MethodDeclaration):
                method_name = method_node.name
                params = []
                if method_node.parameters:
                    for param in method_node.parameters:
                        param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                        params.append(f"{param_type} {param.name}")
                return_type = method_node.return_type.name if method_node.return_type and hasattr(method_node.return_type, 'name') else 'void'
                signature = f"public {return_type} {method_name}({', '.join(params)})"
                start_line = method_node.position.line if method_node.position else None
                end_line = start_line
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

            for constructor_path, constructor_node in node.filter(javalang.tree.ConstructorDeclaration):
                constructor_name = constructor_node.name
                params = []
                if constructor_node.parameters:
                    for param in constructor_node.parameters:
                        param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                        params.append(f"{param_type} {param.name}")
                signature = f"public {constructor_name}({', '.join(params)})"
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
        with open(file_path, 'r', encoding='utf-8') as file:
            src = file.read()
        language = WebUnittester.detect_language(file_path)
        print(f"Detected language: {language}")
        if language == 'python':
            blocks = WebUnittester.parse_python_file(src, file_path)
        elif language == 'java':
            blocks = WebUnittester.parse_java_file(src, file_path)
        else:
            raise ValueError(f"Unsupported language: {language}")
        summary_path = os.path.join(out_dir, "summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(blocks, f, indent=2)
        print(f"Found {len(blocks)} functions/methods to test")
        if len(blocks) == 0:
            raise ValueError(f"No functions or methods found in the uploaded {language} file")
        return WebUnittester.generate_tests(blocks, language, out_dir, api_key)

    @staticmethod
    def count_tokens(text: str) -> int:
        try:
            enc = tiktoken.encoding_for_model("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return max(1, len(text.split()))

    @staticmethod
    def batch_blocks_by_tokens(blocks, max_tokens_per_batch: int):
        if not blocks:
            return []
        batches = []
        current_batch = []
        current_tokens = 0
        for b in blocks:
            block_text = json.dumps(b, ensure_ascii=False)
            t = WebUnittester.count_tokens(block_text)
            if t > max_tokens_per_batch:
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
    def generate_tests(blocks, language, output_dir, api_key):
        """
        Generate unit tests using Google Gemini AI with improved batching and retry logic.
        """
        MODEL_CONTEXT_LIMIT = 32768
        DEFAULT_MAX_OUTPUT_TOKENS = 8192

        ext = "py" if language == "python" else "java"
        model = "gemini-2.5-flash"

        # Build language-specific pieces
        if language == "python":
            framework_info = "pytest framework"
            test_imports = "import pytest"
            example_test = """
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
        else:
            framework_info = "JUnit framework"
            test_imports = "import org.junit.jupiter.api.Test; import static org.junit.jupiter.api.Assertions.*;"
            example_test = """
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

        # System instruction for FIRST batch (complete file)
        si_text_first = """Purpose

            Produce a complete {language} unit test file for all the code blocks described by JSON objects with fields like block_id, function_name, class_context, start_line, end_line, signature, and code.
            
            Output format you should produce:
            A single complete test file with proper package declaration (for Java), imports, and test class structure.
            
            For {language}:
            - Include all necessary imports
            - For Java: Include package declaration and test class declaration
            - For Python: Include all necessary imports at the top
            - Generate 3-5 test methods per block
            - Use {framework_info}
            - Use these imports: {test_imports}
            
            Test naming conventions:
            - For methods: test_<ClassName>_<functionName>_<scenario> (Python) or test<FunctionName><Scenario> (Java)
            - Generate tests for: normal case, edge cases, and error conditions
            
            Code quality:
            - Keep tests simple and independent
            - Use clear assertions
            - No explanatory comments except one-line test description
            - Do NOT add markdown code blocks (no ``` markers)
            
            Example structure:
            {example_test}
            
            Generate the COMPLETE file with package, imports, class structure, and all test methods.
            """

        # System instruction for SUBSEQUENT batches (only test methods)
        si_text_subsequent = """Purpose

            Generate ONLY test methods (no package declaration, no imports, no class declaration) for the code blocks provided.
            
            Important: 
            - Generate ONLY @Test methods (for Java) or test functions (for Python)
            - Do NOT include package declaration
            - Do NOT include import statements  
            - Do NOT include class declaration or closing braces
            - Do NOT add markdown code blocks (no ``` markers)
            - These methods will be appended to an existing test file
            
            For each block, generate 3-5 test methods:
            - Normal operation test
            - Edge case tests
            - Error/exception tests
            
            Test naming conventions:
            - For methods: test_<ClassName>_<functionName>_<scenario> (Python) or test<FunctionName><Scenario> (Java)
            
            Code quality:
            - Keep tests simple and independent
            - Use clear assertions
            - One-line comment per test explaining what it tests
            
            Generate ONLY the test method bodies that can be inserted into an existing test class.
            """

        si_text_first = si_text_first.format(
            language=language, ext=ext, framework_info=framework_info,
            test_imports=test_imports, example_test=example_test
        )
        
        si_text_subsequent = si_text_subsequent.format(
            language=language, ext=ext, framework_info=framework_info,
            test_imports=test_imports, example_test=example_test
        )

        try:
            system_tokens = WebUnittester.count_tokens(si_text_first)
        except Exception:
            system_tokens = 1024

        reserve_for_output = DEFAULT_MAX_OUTPUT_TOKENS
        per_batch_tokens = max(512, MODEL_CONTEXT_LIMIT - reserve_for_output - system_tokens - 512)

        batches = WebUnittester.batch_blocks_by_tokens(blocks, per_batch_tokens)

        def split_large_block(block, max_tokens):
            code = block.get('code', '')
            lines = code.splitlines()
            parts = []
            cur_lines = []
            for ln in lines:
                cur_lines.append(ln)
                text = '\n'.join(cur_lines)
                if WebUnittester.count_tokens(text) >= max_tokens:
                    part = dict(block)
                    part['code'] = '\n'.join(cur_lines)
                    part['block_id'] = part['block_id'] + '_part' + str(len(parts))
                    parts.append(part)
                    cur_lines = []
            if cur_lines:
                part = dict(block)
                part['code'] = '\n'.join(cur_lines)
                part['block_id'] = part['block_id'] + '_part' + str(len(parts))
                parts.append(part)
            return parts

        expanded_batches = []
        for batch in batches:
            total_tokens = sum(WebUnittester.count_tokens(json.dumps(b, ensure_ascii=False)) for b in batch)
            if len(batch) == 1 and total_tokens > per_batch_tokens:
                parts = split_large_block(batch[0], max(256, per_batch_tokens // 2))
                for p in parts:
                    expanded_batches.append([p])
            else:
                expanded_batches.append(batch)
        batches = expanded_batches

        try:
            client = genai.Client(vertexai=True, api_key=api_key)

            if blocks:
                module_name = blocks[0]["block_id"].split("_")[0]
                class_name = None
                for block in blocks:
                    if block.get("class_context"):
                        class_name = block["class_context"]
                        break

                if class_name:
                    test_filename = f"test_{class_name}.{ext}" if language == "python" else f"{class_name}Test.{ext}"
                else:
                    base_module = os.path.splitext(module_name)[0]
                    test_filename = f"test_{base_module}.{ext}" if language == "python" else f"{base_module}Test.{ext}"
            else:
                test_filename = f"test_generated.{ext}" if language == "python" else f"GeneratedTest.{ext}"

            test_path = os.path.join(output_dir, test_filename)

            batch_number = 0
            i = 0
            
            while i < len(batches):
                batch = batches[i]
                is_first_batch = (batch_number == 0)
                
                # Use different system instruction based on batch number
                system_instruction_text = si_text_first if is_first_batch else si_text_subsequent
                
                generate_content_config = types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
                    ],
                    system_instruction=[types.Part.from_text(text=system_instruction_text)],
                )
                
                print(f"🤖 Processing batch {batch_number + 1}/{len(batches)} ({'FULL' if is_first_batch else 'METHODS'}): |", end=" ", flush=True)

                contents = [
                    types.Content(
                        role="user",
                        parts=[{"text": json.dumps(batch, indent=2)}]
                    )
                ]

                attempt = 0
                success = False
                
                while attempt < 3 and not success:
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=contents,
                            config=generate_content_config,
                        )

                        resp_text = None
                        if hasattr(response, 'text') and response.text:
                            resp_text = response.text
                        else:
                            try:
                                resp_text = getattr(response, 'outputs', None)
                                if isinstance(resp_text, list):
                                    extracted = []
                                    for o in resp_text:
                                        if isinstance(o, dict):
                                            for v in o.values():
                                                if isinstance(v, str):
                                                    extracted.append(v)
                                    resp_text = "\n".join(extracted) if extracted else None
                            except Exception:
                                resp_text = None

                        if not resp_text:
                            try:
                                resp_text = str(response)
                            except Exception:
                                resp_text = ""

                        if len(resp_text.strip()) < 30:
                            raise ValueError("Received too-short response from model; treating as truncated")

                        # Clean up response (remove markdown if present)
                        resp_text = re.sub(r'^```\w*\n', '', resp_text)
                        resp_text = re.sub(r'\n```$', '', resp_text)
                        resp_text = resp_text.strip()

                        # Write to file
                        if is_first_batch:
                            # First batch: write complete file
                            with open(test_path, 'w', encoding='utf-8') as f:
                                f.write(resp_text)
                        else:
                            # Subsequent batches: append methods
                            if language == "java":
                                # For Java, we need to insert before the closing brace
                                with open(test_path, 'r', encoding='utf-8') as f:
                                    existing_content = f.read()
                                
                                # Find the last closing brace and insert before it
                                last_brace = existing_content.rfind('}')
                                if last_brace != -1:
                                    updated_content = (
                                        existing_content[:last_brace] + 
                                        "\n\n    " + resp_text.replace('\n', '\n    ') + 
                                        "\n" + existing_content[last_brace:]
                                    )
                                    with open(test_path, 'w', encoding='utf-8') as f:
                                        f.write(updated_content)
                                else:
                                    # Fallback: just append
                                    with open(test_path, 'a', encoding='utf-8') as f:
                                        f.write("\n\n" + resp_text)
                            else:
                                # For Python, just append
                                with open(test_path, 'a', encoding='utf-8') as f:
                                    f.write("\n\n" + resp_text)
                        
                        print(" ✅ done!")
                        success = True
                        batch_number += 1

                    except Exception as gen_err:
                        attempt += 1
                        wait = 1.5 ** attempt
                        print(f"⚠️ Attempt {attempt} failed for batch {i+1}: {gen_err}. retrying in {wait:.1f}s...")
                        time.sleep(wait)

                        if attempt < 3 and len(batch) > 1:
                            mid = len(batch) // 2
                            left = batch[:mid]
                            right = batch[mid:]
                            batches[i] = left
                            batches.insert(i+1, right)
                            print(f"🔀 Splitting batch {i+1} into sizes {len(left)} and {len(right)}")
                            attempt = 0
                            batch = left
                            contents = [
                                types.Content(
                                    role="user",
                                    parts=[{"text": json.dumps(batch, indent=2)}]
                                )
                            ]
                            continue

                if not success:
                    print(f"❌ Failed to generate tests for batch {i+1} after all retries")
                    raise Exception(f"Failed to generate tests for batch {i+1}")

                i += 1

            print(f"✅ All {language} tests generated successfully: {test_path}")
            return test_path

        except Exception as e:
            print(f"❌ Error generating {language} tests: {e}")
            raise Exception(f"Failed to generate {language} tests: {str(e)}")