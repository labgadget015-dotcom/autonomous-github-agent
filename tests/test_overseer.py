#!/usr/bin/env python3
"""
Tests for Repository Overseer

Comprehensive test suite for the overseer modules.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from overseer import RepositoryOverseer
from overseer.code_analyzer import CodeAnalyzer
from overseer.doc_generator import DocumentationGenerator
from overseer.dependency_manager import DependencyManager
from overseer.cicd_optimizer import CICDOptimizer
from overseer.issue_triager import IssueTriager
from overseer.automation_engine import AutomationEngine
from overseer.monitor import RepositoryMonitor


class TestRepositoryOverseer(unittest.TestCase):
    """Test the main RepositoryOverseer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create a minimal repository structure
        (self.test_path / 'src').mkdir()
        (self.test_path / 'tests').mkdir()
        
        # Create a simple Python file
        with open(self.test_path / 'src' / 'example.py', 'w') as f:
            f.write("""
def hello_world():
    \"\"\"Print hello world\"\"\"
    print("Hello, World!")
""")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test overseer initialization"""
        overseer = RepositoryOverseer(self.test_dir)
        self.assertIsNotNone(overseer)
        self.assertEqual(overseer.repo_path, self.test_path)
    
    def test_default_config(self):
        """Test default configuration loading"""
        overseer = RepositoryOverseer(self.test_dir)
        config = overseer.config
        
        self.assertIn('code_analysis', config)
        self.assertIn('documentation', config)
        self.assertIn('dependency_management', config)
        self.assertTrue(config['code_analysis']['enabled'])
    
    def test_analyze_code(self):
        """Test code analysis"""
        overseer = RepositoryOverseer(self.test_dir)
        results = overseer.analyze_code()
        
        self.assertIn('refactoring_opportunities', results)
        self.assertIn('architectural_improvements', results)
        self.assertIn('performance_optimizations', results)
        self.assertIn('code_quality_score', results)
        self.assertIsInstance(results['code_quality_score'], (int, float))
    
    def test_run_full_analysis(self):
        """Test running full analysis"""
        overseer = RepositoryOverseer(self.test_dir)
        results = overseer.run_full_analysis()
        
        self.assertIn('timestamp', results)
        self.assertIn('analyses', results)
        self.assertIn('recommendations', results)
    
    def test_save_results(self):
        """Test saving results to file"""
        overseer = RepositoryOverseer(self.test_dir)
        overseer.run_full_analysis()
        
        output_path = overseer.save_results()
        self.assertTrue(output_path.exists())
        
        # Verify file contains JSON
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        self.assertIn('timestamp', data)


class TestCodeAnalyzer(unittest.TestCase):
    """Test the CodeAnalyzer module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test Python files with various issues
        (self.test_path / 'src').mkdir()
        
        # File with long function
        with open(self.test_path / 'src' / 'long_function.py', 'w') as f:
            f.write("""
def very_long_function():
    \"\"\"This function is too long\"\"\"
""" + "    x = 1\n" * 60)
        
        # File with god class
        with open(self.test_path / 'src' / 'god_class.py', 'w') as f:
            f.write("""
class GodClass:
    \"\"\"A class with too many methods\"\"\"
""" + "\n".join([f"    def method_{i}(self): pass" for i in range(25)]))
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test analyzer initialization"""
        config = {'code_analysis': {'enabled': True}}
        analyzer = CodeAnalyzer(self.test_path, config)
        self.assertIsNotNone(analyzer)
    
    def test_find_python_files(self):
        """Test finding Python files"""
        config = {'code_analysis': {'enabled': True}}
        analyzer = CodeAnalyzer(self.test_path, config)
        
        files = analyzer._find_python_files()
        self.assertGreater(len(files), 0)
    
    def test_detect_long_functions(self):
        """Test detection of long functions"""
        config = {'code_analysis': {'enabled': True}}
        analyzer = CodeAnalyzer(self.test_path, config)
        
        results = analyzer.analyze()
        
        # Should detect the long function
        long_funcs = [r for r in results['refactoring'] if r['type'] == 'long_function']
        self.assertGreater(len(long_funcs), 0)
    
    def test_detect_god_classes(self):
        """Test detection of god classes"""
        config = {'code_analysis': {'enabled': True}}
        analyzer = CodeAnalyzer(self.test_path, config)
        
        results = analyzer.analyze()
        
        # Should detect the god class
        god_classes = [r for r in results['architecture'] if r['type'] == 'god_class']
        self.assertGreater(len(god_classes), 0)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        config = {'code_analysis': {'enabled': True}}
        analyzer = CodeAnalyzer(self.test_path, config)
        
        results = analyzer.analyze()
        
        # Quality score should be between 0 and 100
        self.assertGreaterEqual(results['quality_score'], 0)
        self.assertLessEqual(results['quality_score'], 100)


class TestDocumentationGenerator(unittest.TestCase):
    """Test the DocumentationGenerator module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test Python file
        (self.test_path / 'src').mkdir()
        with open(self.test_path / 'src' / 'example.py', 'w') as f:
            f.write("""
\"\"\"Example module\"\"\"

def example_function():
    \"\"\"Example function\"\"\"
    pass
""")
        
        # Create requirements.txt
        with open(self.test_path / 'requirements.txt', 'w') as f:
            f.write("pytest>=7.0.0\n")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test generator initialization"""
        config = {'documentation': {'enabled': True}}
        generator = DocumentationGenerator(self.test_path, config)
        self.assertIsNotNone(generator)
    
    def test_detect_repository_info(self):
        """Test repository info detection"""
        config = {'documentation': {'enabled': True}}
        generator = DocumentationGenerator(self.test_path, config)
        
        info = generator.repo_info
        self.assertIn('has_python', info)
        self.assertTrue(info['has_python'])
    
    def test_generate_readme(self):
        """Test README generation"""
        config = {'documentation': {'enabled': True}}
        generator = DocumentationGenerator(self.test_path, config)
        
        readme_path = generator.generate_readme()
        self.assertIsNotNone(readme_path)
        self.assertTrue(readme_path.exists())
        
        # Verify content
        with open(readme_path) as f:
            content = f.read()
        
        self.assertIn('#', content)  # Should have markdown headers
    
    def test_generate_contributing(self):
        """Test CONTRIBUTING.md generation"""
        config = {'documentation': {'enabled': True}}
        generator = DocumentationGenerator(self.test_path, config)
        
        contrib_path = generator.generate_contributing()
        self.assertIsNotNone(contrib_path)
        self.assertTrue(contrib_path.exists())
        
        # Verify content
        with open(contrib_path) as f:
            content = f.read()
        
        self.assertIn('Contributing', content)


class TestDependencyManager(unittest.TestCase):
    """Test the DependencyManager module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create requirements.txt with some packages
        with open(self.test_path / 'requirements.txt', 'w') as f:
            f.write("""
pytest>=7.0.0
requests>=2.25.0
urllib3<1.26.5
""")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test manager initialization"""
        config = {'dependency_management': {'enabled': True}}
        manager = DependencyManager(self.test_path, config)
        self.assertIsNotNone(manager)
    
    def test_parse_requirements(self):
        """Test parsing requirements.txt"""
        config = {'dependency_management': {'enabled': True}}
        manager = DependencyManager(self.test_path, config)
        
        deps = manager._parse_requirements(self.test_path / 'requirements.txt')
        
        self.assertGreater(len(deps), 0)
        self.assertTrue(any(d['name'] == 'pytest' for d in deps))
    
    def test_analyze_dependencies(self):
        """Test dependency analysis"""
        config = {'dependency_management': {'enabled': True, 'check_vulnerabilities': True}}
        manager = DependencyManager(self.test_path, config)
        
        results = manager.analyze()
        
        self.assertIn('outdated', results)
        self.assertIn('vulnerabilities', results)
        self.assertIn('recommendations', results)


class TestCICDOptimizer(unittest.TestCase):
    """Test the CICDOptimizer module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create .github/workflows directory
        workflows_dir = self.test_path / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True)
        
        # Create a basic workflow file
        with open(workflows_dir / 'test.yml', 'w') as f:
            f.write("""
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest
""")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test optimizer initialization"""
        config = {'cicd': {'enabled': True}}
        optimizer = CICDOptimizer(self.test_path, config)
        self.assertIsNotNone(optimizer)
    
    def test_analyze_workflows(self):
        """Test workflow analysis"""
        config = {'cicd': {'enabled': True}}
        optimizer = CICDOptimizer(self.test_path, config)
        
        results = optimizer.analyze()
        
        self.assertIn('optimizations', results)
        self.assertIn('testing', results)
        self.assertIn('linting', results)
    
    def test_check_for_caching(self):
        """Test cache detection"""
        config = {'cicd': {'enabled': True}}
        optimizer = CICDOptimizer(self.test_path, config)
        
        workflow = {'jobs': {'test': {'steps': []}}}
        has_cache = optimizer._check_for_caching(workflow)
        
        self.assertFalse(has_cache)


class TestIssueTriager(unittest.TestCase):
    """Test the IssueTriager module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test triager initialization"""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)
        self.assertIsNotNone(triager)
    
    def test_analyze_issue_content(self):
        """Test issue content analysis"""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)
        
        # Test bug detection
        result = triager.analyze_issue_content(
            "Bug in login feature",
            "The login feature is broken and not working"
        )
        
        self.assertIn('labels', result)
        self.assertIn('priority', result)
        self.assertIn('bug', result['labels'])
    
    def test_unicode_issue_content(self):
        """Test that Unicode characters in title/body are handled without errors."""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)

        # Russian + Chinese characters in title; English keywords still detected
        result = triager.analyze_issue_content(
            "🚀 Request: Добавить поддержку 中文 feature",
            "Это запрос на добавление новой функции. 请添加对中文的支持。"
        )
        self.assertIn('labels', result)
        self.assertIn('priority', result)
        self.assertIsInstance(result['confidence'], float)
        # The English keyword "feature" should still be detected
        self.assertIn('enhancement', result['labels'])

    def test_special_chars_issue_content(self):
        """Test that special characters (@#$%^&*()) in title/body don't cause errors."""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)

        result = triager.analyze_issue_content(
            "[EDGE-CASE-2] @#$%^&*() bug report: crash on input",
            "Reproduction: pass @#$%^&*() as input → crash/error"
        )
        self.assertIn('labels', result)
        self.assertIn('priority', result)
        self.assertIsInstance(result['confidence'], float)
        # "bug" keyword should still be picked up despite surrounding special chars
        self.assertIn('bug', result['labels'])

    def test_mixed_unicode_and_special_chars(self):
        """Test issue with both Unicode and special characters is handled safely."""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)

        # Mirrors the actual edge-case issue title from the feature request
        title = "[EDGE-CASE-2] 🚀 Request: Добавить поддержку 中文 & special chars: @#$%^&*()"
        body = ""
        # Must not raise any exception
        result = triager.analyze_issue_content(title, body)
        self.assertIn('labels', result)
        self.assertIn('priority', result)
        """Test security issue detection"""
        config = {'issue_triaging': {'enabled': True}}
        triager = IssueTriager(self.test_path, config)
        
        result = triager.analyze_issue_content(
            "Security vulnerability in authentication",
            "Critical security issue with XSS vulnerability"
        )
        
        self.assertIn('security', result['labels'])
        self.assertIn(result['priority'], ['critical', 'high'])


class TestAutomationEngine(unittest.TestCase):
    """Test the AutomationEngine module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test Python file
        with open(self.test_path / 'example.py', 'w') as f:
            f.write("print('hello')")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test engine initialization"""
        config = {'automation': {'enabled': True}}
        engine = AutomationEngine(self.test_path, config)
        self.assertIsNotNone(engine)
    
    def test_generate_scripts(self):
        """Test script generation"""
        config = {
            'automation': {
                'enabled': True,
                'code_formatting': True,
                'release_tagging': True,
                'environment_setup': True
            }
        }
        engine = AutomationEngine(self.test_path, config)
        
        results = engine.generate()
        
        self.assertIn('formatting', results)
        self.assertIn('release', results)
        self.assertIn('setup', results)


class TestRepositoryMonitor(unittest.TestCase):
    """Test the RepositoryMonitor module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create basic repository structure
        with open(self.test_path / 'README.md', 'w') as f:
            f.write("# Test Repository")
        
        with open(self.test_path / 'requirements.txt', 'w') as f:
            f.write("pytest>=7.0.0\n")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test monitor initialization"""
        config = {'monitoring': {'enabled': True}}
        monitor = RepositoryMonitor(self.test_path, config)
        self.assertIsNotNone(monitor)
    
    def test_analyze(self):
        """Test repository analysis"""
        config = {'monitoring': {'enabled': True}}
        monitor = RepositoryMonitor(self.test_path, config)
        
        results = monitor.analyze()
        
        self.assertIn('quality', results)
        self.assertIn('performance', results)
        self.assertIn('security', results)
        self.assertIn('collaboration', results)
        self.assertIn('recommendations', results)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        config = {'monitoring': {'enabled': True}}
        monitor = RepositoryMonitor(self.test_path, config)
        
        results = monitor.analyze()
        
        # Should generate some recommendations
        self.assertIsInstance(results['recommendations'], list)


if __name__ == '__main__':
    unittest.main()
