import ast
import re
from typing import List, Dict, Any
import javalang  # For Java support: pip install javalang

class CodeChunker():
    """Smart code chunking for Python and Java"""
    
    def __init__(self, language: str = "python"):
        self.language = language.lower()
    
    def chunk_by_functions(self, code: str) -> List[Dict[str, Any]]:
        """Split code into logical chunks (classes/functions)"""
        if self.language == "python":
            return self._chunk_python(code)
        elif self.language == "java":
            return self._chunk_java(code)
        else:
            raise ValueError(f"Unsupported language: {self.language}")
    
    def _chunk_python(self, code: str) -> List[Dict[str, Any]]:
        """Chunk Python code by classes and functions"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # If parsing fails, return the whole file as one chunk
            return [{
                'name': 'entire_file',
                'type': 'module',
                'code': code,
                'line_start': 1,
                'line_end': len(code.split('\n'))
            }]
        
        chunks = []
        lines = code.split('\n')
        
        # Extract imports for context
        imports = self._extract_python_imports(tree)
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                chunk = self._extract_class_chunk(node, code, lines)
                chunk['imports'] = imports
                chunks.append(chunk)
            elif isinstance(node, ast.FunctionDef):
                chunk = self._extract_function_chunk(node, code, lines)
                chunk['imports'] = imports
                chunks.append(chunk)
        
        return chunks if chunks else [{
            'name': 'entire_file',
            'type': 'module',
            'code': code,
            'line_start': 1,
            'line_end': len(lines),
            'imports': imports
        }]
    
    def _extract_class_chunk(self, node: ast.ClassDef, code: str, lines: List[str]) -> Dict:
        """Extract a class with its methods"""
        chunk_code = ast.get_source_segment(code, node)
        
        # Get methods in the class
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'line': item.lineno,
                    'is_private': item.name.startswith('_'),
                    'decorators': [d.id for d in item.decorator_list if isinstance(d, ast.Name)]
                })
        
        return {
            'name': node.name,
            'type': 'class',
            'code': chunk_code,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'methods': methods,
            'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)]
        }
    
    def _extract_function_chunk(self, node: ast.FunctionDef, code: str, lines: List[str]) -> Dict:
        """Extract a standalone function"""
        chunk_code = ast.get_source_segment(code, node)
        
        return {
            'name': node.name,
            'type': 'function',
            'code': chunk_code,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
            'args': [arg.arg for arg in node.args.args]
        }
    
    def _extract_python_imports(self, tree: ast.AST) -> List[str]:
        """Extract all imports from Python code"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([f"import {alias.name}" for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend([f"from {module} import {alias.name}" for alias in node.names])
        return imports
    
    def _chunk_java(self, code: str) -> List[Dict[str, Any]]:
        """Chunk Java code by classes and methods"""
        try:
            tree = javalang.parse.parse(code)
        except Exception as e:
            return [{
                'name': 'entire_file',
                'type': 'module',
                'code': code,
                'line_start': 1,
                'line_end': len(code.split('\n'))
            }]
        
        chunks = []
        lines = code.split('\n')
        
        # Extract package and imports
        package = tree.package.name if tree.package else None
        imports = [imp.path for imp in tree.imports] if tree.imports else []
        
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            # Extract class code (simplified - you might need better extraction)
            chunk = {
                'name': node.name,
                'type': 'class',
                'code': self._extract_java_class_code(code, node.name),
                'package': package,
                'imports': imports,
                'methods': []
            }
            
            # Extract methods
            for method in node.methods:
                chunk['methods'].append({
                    'name': method.name,
                    'modifiers': method.modifiers,
                    'return_type': method.return_type.name if method.return_type else 'void'
                })
            
            chunks.append(chunk)
        
        return chunks if chunks else [{
            'name': 'entire_file',
            'type': 'module',
            'code': code,
            'package': package,
            'imports': imports
        }]
    
    def _extract_java_class_code(self, code: str, class_name: str) -> str:
        """Extract Java class code (simplified regex-based)"""
        pattern = rf'class\s+{class_name}\s*.*?\{{.*?\n\}}\s*$'
        match = re.search(pattern, code, re.DOTALL | re.MULTILINE)
        return match.group(0) if match else code
    
    def chunk_by_size(self, code: str, max_tokens: int = 100000) -> List[str]:
        """Split code by approximate token count"""
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            # Rough estimate: 1 token ≈ 4 characters
            line_tokens = len(line) // 4
            
            if current_size + line_tokens > max_tokens:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_tokens
            else:
                current_chunk.append(line)
                current_size += line_tokens
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def get_chunk_info(self, chunks: List[Dict]) -> str:
        """Get summary of chunks"""
        summary = f"Total chunks: {len(chunks)}\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            summary += f"{i}. {chunk['type'].upper()}: {chunk['name']}\n"
            if chunk['type'] == 'class' and 'methods' in chunk:
                summary += f"   Methods: {len(chunk['methods'])}\n"
                for method in chunk['methods'][:5]:  # Show first 5 methods
                    summary += f"   - {method['name']}\n"
                if len(chunk['methods']) > 5:
                    summary += f"   ... and {len(chunk['methods']) - 5} more\n"
            summary += f"   Lines: {chunk.get('line_start', '?')} - {chunk.get('line_end', '?')}\n\n"
        
        return summary