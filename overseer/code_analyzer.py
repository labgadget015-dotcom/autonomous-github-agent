#!/usr/bin/env python3
"""
Code Analyzer Module

Deep code analysis for refactoring opportunities, architectural improvements,
and performance optimizations.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Advanced code analyzer for detecting refactoring opportunities,
    architectural issues, and performance problems.
    """
    
    def __init__(self, repo_path: Path, config: Dict):
        self.repo_path = repo_path
        self.config = config
        self.results = {
            'refactoring': [],
            'architecture': [],
            'performance': [],
            'complexity': [],
            'quality_score': 100
        }
    
    def analyze(self) -> Dict[str, Any]:
        """
        Run comprehensive code analysis.
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Running code analysis...")
        
        # Find Python files
        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
        
        # Calculate overall quality score
        self._calculate_quality_score()
        
        return self.results
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the repository"""
        python_files = []
        
        # Exclude common directories
        exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.tox', 'build', 'dist', '.eggs'}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return  # Skip files with syntax errors
            
            # Run various analyses
            self._detect_long_functions(tree, file_path)
            self._detect_code_duplication(content, file_path)
            self._detect_complex_conditionals(tree, file_path)
            self._detect_magic_numbers(tree, file_path)
            self._detect_architectural_issues(tree, file_path)
            self._detect_performance_issues(tree, file_path)
            
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
    
    def _detect_long_functions(self, tree: ast.AST, file_path: Path):
        """Detect functions that are too long"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count lines in function
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    line_count = node.end_lineno - node.lineno
                    
                    if line_count > 50:  # Threshold for long functions
                        self.results['refactoring'].append({
                            'type': 'long_function',
                            'file': str(file_path.relative_to(self.repo_path)),
                            'function': node.name,
                            'line': node.lineno,
                            'lines': line_count,
                            'severity': 'high' if line_count > 100 else 'medium',
                            'recommendation': f'Function {node.name} has {line_count} lines. Consider breaking it into smaller functions.'
                        })
    
    def _detect_code_duplication(self, content: str, file_path: Path):
        """Detect potential code duplication"""
        lines = content.split('\n')
        
        # Simple duplication detection - look for repeated code blocks
        block_size = 5
        blocks = {}
        
        for i in range(len(lines) - block_size):
            block = '\n'.join(lines[i:i+block_size]).strip()
            if block and len(block) > 50:  # Ignore short blocks
                if block in blocks:
                    blocks[block].append(i)
                else:
                    blocks[block] = [i]
        
        # Report duplications
        for block, occurrences in blocks.items():
            if len(occurrences) > 1:
                self.results['refactoring'].append({
                    'type': 'code_duplication',
                    'file': str(file_path.relative_to(self.repo_path)),
                    'lines': occurrences,
                    'severity': 'medium',
                    'recommendation': f'Code block appears {len(occurrences)} times. Consider extracting to a function.'
                })
    
    def _detect_complex_conditionals(self, tree: ast.AST, file_path: Path):
        """Detect complex conditional statements"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Count boolean operations in condition
                complexity = self._count_boolean_ops(node.test)
                
                if complexity > 3:
                    self.results['refactoring'].append({
                        'type': 'complex_conditional',
                        'file': str(file_path.relative_to(self.repo_path)),
                        'line': node.lineno,
                        'complexity': complexity,
                        'severity': 'medium',
                        'recommendation': 'Complex conditional detected. Consider extracting to well-named boolean variables.'
                    })
    
    def _count_boolean_ops(self, node: ast.AST) -> int:
        """Count boolean operations in an AST node"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.BoolOp, ast.Compare)):
                count += 1
        return count
    
    def _detect_magic_numbers(self, tree: ast.AST, file_path: Path):
        """Detect magic numbers that should be constants"""
        for node in ast.walk(tree):
            # Support both old ast.Num and new ast.Constant for compatibility
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Ignore 0, 1, -1 as they're commonly used
                if node.value not in (0, 1, -1, 0.0, 1.0, -1.0) and isinstance(node.value, int):
                    self.results['refactoring'].append({
                        'type': 'magic_number',
                        'file': str(file_path.relative_to(self.repo_path)),
                        'line': node.lineno,
                        'value': node.value,
                        'severity': 'low',
                        'recommendation': f'Magic number {node.value} should be a named constant.'
                    })
    
    def _detect_architectural_issues(self, tree: ast.AST, file_path: Path):
        """Detect architectural issues and improvement opportunities"""
        # Detect god classes (too many methods)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
                
                if method_count > 20:
                    self.results['architecture'].append({
                        'type': 'god_class',
                        'file': str(file_path.relative_to(self.repo_path)),
                        'class': node.name,
                        'line': node.lineno,
                        'method_count': method_count,
                        'severity': 'high',
                        'recommendation': f'Class {node.name} has {method_count} methods. Consider applying Single Responsibility Principle and splitting into smaller classes.'
                    })
        
        # Detect missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.results['architecture'].append({
                        'type': 'missing_docstring',
                        'file': str(file_path.relative_to(self.repo_path)),
                        'name': node.name,
                        'line': node.lineno,
                        'severity': 'low',
                        'recommendation': f'{node.__class__.__name__[:-3]} {node.name} is missing a docstring.'
                    })
    
    def _detect_performance_issues(self, tree: ast.AST, file_path: Path):
        """Detect potential performance issues"""
        # Detect list comprehension opportunities
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if it's appending to a list
                if (len(node.body) == 1 and 
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Call)):
                    
                    call = node.body[0].value
                    if (isinstance(call.func, ast.Attribute) and 
                        call.func.attr == 'append'):
                        
                        self.results['performance'].append({
                            'type': 'list_comprehension_opportunity',
                            'file': str(file_path.relative_to(self.repo_path)),
                            'line': node.lineno,
                            'severity': 'low',
                            'recommendation': 'Consider using list comprehension instead of append in loop for better performance.'
                        })
        
        # Detect inefficient string concatenation
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            self.results['performance'].append({
                                'type': 'string_concatenation',
                                'file': str(file_path.relative_to(self.repo_path)),
                                'line': node.lineno,
                                'severity': 'medium',
                                'recommendation': 'String concatenation in loop detected. Consider using join() or list accumulation.'
                            })
    
    def _calculate_quality_score(self):
        """Calculate overall code quality score"""
        score = 100
        
        # Deduct points for issues
        score -= len(self.results['refactoring']) * 2
        score -= len(self.results['architecture']) * 3
        score -= len(self.results['performance']) * 1
        
        # Ensure score doesn't go below 0
        self.results['quality_score'] = max(0, score)
