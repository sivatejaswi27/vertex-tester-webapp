
from typing import List, Dict, Optional
import time
from pathlib import Path
from code_chunker import CodeChunker
import vertexai
from vertexai.generative_models import GenerativeModel
from google import genai
from google.genai import types
from google.cloud import aiplatform

class HierarchicalTestGenerator:
    """Hierarchical test generation with smart chunking"""
    
    def __init__(self, api_key: str, model_name: str):
    # Configure client for Vertex AI

        project = "seventytwo"
        location = "us-central1"
        if project and location:
            aiplatform.init(project=project, location=location)
        else:
            aiplatform.init()


        client = genai.Client(
            api_key=api_key,
            vertexai=True,
        )

        if client:
            print(f"✓ Connected to Vertex AI Project ${client}")
            
        
        self.client = client
        self.model_name = model_name
        self.chunker = None
    
    def set_language(self, language: str):
        """Set the programming language"""
        self.language = language
        self.chunker = CodeChunker(language)
    
    def analyze_codebase(self, code: str, file_name: str = "") -> str:
        """Stage 1: High-level analysis and test plan"""
        
        # Use first 15000 characters for analysis
        code_preview = code[:15000]
        
        prompt = f"""
            You are a senior software engineer creating a comprehensive test plan.

            File: {file_name}
            Language: {self.language}
            Total size: {len(code)} characters

            Code preview:
            ```{self.language}
            {code_preview}
            {"... (code continues)" if len(code) > 15000 else ""}

            Please analyze this code and provide:

            Architecture Overview: Main classes, their purposes, and relationships
            Critical Components: Functions/methods that need thorough testing
            Testing Strategy:
            What testing framework to use
            Required test fixtures and mocks
            Integration vs unit test considerations
            Edge Cases: Common edge cases to test for each component
            Complexity Assessment: Rate complexity (1-10) and testing priority
            Test Organization: Suggested test file structure
            Format as a clear, actionable test plan.
            """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error during analysis: {str(e)}\nProceeding with default test plan..."

    def generate_test_for_chunk(
        self, 
        chunk: Dict, 
        test_plan: str, 
        context: str = "",
        progress_callback=None
    ) -> str:
        """Stage 2: Generate tests for individual chunk"""
        
        chunk_type = chunk['type']
        chunk_name = chunk['name']
        chunk_code = chunk['code']

        generate_content_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.8,
            
        )

        # Build context
        context_info = ""
        if 'imports' in chunk:
            context_info += "Required imports:\n"
            context_info += "\n".join(chunk['imports'][:10])  # Limit imports
            context_info += "\n\n"
        
        if 'package' in chunk and chunk['package']:
            context_info += f"Package: {chunk['package']}\n\n"
        
        if context:
            context_info += f"Additional context:\n{context}\n\n"
        
        # Framework selection
        framework = "pytest" if self.language == "python" else "JUnit 5"
    
        prompt = f"""
            You are writing unit tests following this test plan:

            {test_plan}

            {context_info}

            Now generate comprehensive unit tests for this {chunk_type}:
            {chunk_code}

            Requirements:

            Use {framework} framework
            Follow the test plan strategy
            Include:
            Setup/teardown methods if needed
            Test fixtures and mocks for dependencies
            Happy path tests
            Edge cases and error scenarios
            Boundary value tests
            Use descriptive test names that explain what is being tested
            Add docstrings/comments explaining complex test scenarios
            Ensure tests are independent and can run in any order
            {"For Python: Use pytest fixtures, parametrize for multiple test cases, and mock external dependencies" if self.language == "python" else "For Java: Use @BeforeEach/@AfterEach, @ParameterizedTest, and Mockito for mocking"}

            Generate ONLY the test code, no explanations.
            """
    
        try:
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=generate_content_config
            )
            if progress_callback:
                progress_callback(f"✓ Generated tests for {chunk_name}")
            return response.text
        except Exception as e:
            error_msg = f"Error generating tests for {chunk_name}: {str(e)}"
            if progress_callback:
                progress_callback(error_msg)
            return f"# {error_msg}\n# TODO: Manual test creation needed\n"

    def generate_tests_hierarchical(
        self,
        code: str,
        file_name: str = "code_file",
        output_dir: str = "tests",
        max_chunk_tokens: int = 100000,
        progress_callback=None
    ) -> Dict[str, str]:
        """
        Main method: Generate tests using hierarchical approach
        
        Returns:
            Dict with 'test_plan', 'test_code', 'output_file', 'chunks_info'
        """
        
        if progress_callback:
            progress_callback("🔍 Stage 1: Analyzing codebase...")
        
        # Stage 1: Analyze and create test plan
        test_plan = self.analyze_codebase(code, file_name)
        
        if progress_callback:
            progress_callback("✓ Test plan created")
            progress_callback("📦 Stage 2: Chunking code...")
        
        # Stage 2: Chunk the code
        chunks = self.chunker.chunk_by_functions(code)
        chunks_info = self.chunker.get_chunk_info(chunks)
        
        if progress_callback:
            progress_callback(f"✓ Created {len(chunks)} chunks")
            progress_callback("🧪 Stage 3: Generating tests for each chunk...")
        
        # Stage 3: Generate tests for each chunk
        all_tests = []
        
        # Create context from imports
        if chunks and 'imports' in chunks[0]:
            context = "\n".join(chunks[0]['imports'][:15])
        else:
            context = ""
        
        for i, chunk in enumerate(chunks, 1):
            if progress_callback:
                progress_callback(f"Generating tests for chunk {i}/{len(chunks)}: {chunk['name']}")
            
            test_code = self.generate_test_for_chunk(
                chunk, 
                test_plan, 
                context,
                progress_callback
            )
            
            # Add separator and header
            header = f"\n{'#' * 80}\n# Tests for {chunk['type']}: {chunk['name']}\n{'#' * 80}\n"
            all_tests.append(header + test_code)
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        if progress_callback:
            progress_callback("📝 Stage 4: Combining and formatting tests...")
        
        # Stage 4: Combine all tests
        combined_tests = self._format_test_file(all_tests, file_name)
        
        # Stage 5: Save to file
        output_file = self._save_tests(combined_tests, file_name, output_dir)
        
        if progress_callback:
            progress_callback(f"✅ Tests saved to: {output_file}")
        
        return {
            'test_plan': test_plan,
            'test_code': combined_tests,
            'output_file': output_file,
            'chunks_info': chunks_info,
            'num_chunks': len(chunks)
        }

    def _format_test_file(self, test_chunks: List[str], file_name: str) -> str:
        """Format the complete test file with proper imports and structure"""
        
        if self.language == "python":
            header = f'''"""
            Unit tests for {file_name}
            Generated using Vertex Tester with Hierarchical Test Generation
            """

            import pytest
            from unittest.mock import Mock, patch, MagicMock, call
            import sys
            import os

            Add parent directory to path if needed
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(file))))

            '''
        else:  # Java
            header = f'''/**

                Unit tests for {file_name}
                Generated using Vertex Tester with Hierarchical Test Generation */
                import org.junit.jupiter.api.;
                import org.mockito.;
                import static org.junit.jupiter.api.Assertions.;
                import static org.mockito.Mockito.;

                '''
        return header + "\n\n".join(test_chunks)

    def _save_tests(self, test_code: str, file_name: str, output_dir: str) -> str:
        """Save test code to file"""
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        base_name = Path(file_name).stem
        extension = ".py" if self.language == "python" else ".java"
        
        if self.language == "python":
            output_file = f"{output_dir}/test_{base_name}{extension}"
        else:
            output_file = f"{output_dir}/{base_name}Test{extension}"
        
        # Save file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return output_file