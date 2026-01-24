#!/usr/bin/env python3
"""
Optimized Parallel Code Analyzer with Caching and Async I/O
Performance improvements: async subprocess, result caching, streaming output
"""

import asyncio
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Dict, List, Optional

try:
    import orjson  # 3-5x faster than json
    USE_ORJSON = True
except ImportError:
    import json as orjson
    USE_ORJSON = False

try:
    import yaml
except ImportError:
    print("⚠️ PyYAML not installed. Using default configuration.")
    yaml = None


@contextmanager
def timer(name: str):
    """Performance timing context manager."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"⏱️ {name}: {elapsed:.2f}s")


class ResultCache:
    """File-based result cache to avoid re-analyzing unchanged files."""
    
    def __init__(self, cache_dir: str = '.analysis_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate file content hash."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def _cache_key(self, tool: str, file_path: str, file_hash: str) -> Path:
        """Generate cache key."""
        return self.cache_dir / f"{tool}_{file_hash[:16]}.json"
        
    def get(self, tool: str, file_path: str) -> Optional[Dict]:
        """Get cached result if file unchanged."""
        try:
            file_hash = self._get_file_hash(file_path)
            cache_file = self._cache_key(tool, file_path, file_hash)
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    if USE_ORJSON:
                        return orjson.loads(f.read())
                    return json.load(f)
        except Exception:
            pass
        return None
        
    def set(self, tool: str, file_path: str, result: Dict):
        """Cache result."""
        try:
            file_hash = self._get_file_hash(file_path)
            cache_file = self._cache_key(tool, file_path, file_hash)
            
            with open(cache_file, 'wb') as f:
                if USE_ORJSON:
                    f.write(orjson.dumps(result))
                else:
                    json.dump(result, f)
        except Exception:
            pass
            
    def clear_old(self, max_age_days: int = 7):
        """Remove cache files older than max_age_days."""
        cutoff = time.time() - (max_age_days * 86400)
        for cache_file in self.cache_dir.glob('*.json'):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink()


class OptimizedCodeAnalyzer:
    """Optimized parallel code analyzer with async I/O and caching."""
    
    def __init__(self, config_file: str = '.github/config/analysis-config.yml'):
        self.config = self.load_config(config_file)
        self.cache = ResultCache()
        self.results = {}
        self.use_cache = os.getenv('ANALYSIS_CACHE', 'true').lower() == 'true'
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file."""
        if yaml and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
        
        # Default configuration
        return {
            'targets': ['.github/scripts', 'scripts', 'tests'],
            'thresholds': {
                'pylint': 8.0,
                'coverage': 80,
                'complexity': 10,
            },
            'tools': {
                'ruff': True,  # Use Ruff (fast)
                'pylint': True,
                'flake8': False,  # Ruff replaces this
                'bandit': True,
                'radon': True,
            }
        }
        
    async def run_command_async(self, cmd: List[str], tool_name: str) -> Dict:
        """Run command asynchronously using subprocess."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout
            )
            
            return {
                'tool': tool_name,
                'status': 'success' if process.returncode == 0 else 'failed',
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
            }
        except asyncio.TimeoutError:
            return {
                'tool': tool_name,
                'status': 'timeout',
                'error': f'{tool_name} timed out after 300 seconds'
            }
        except Exception as e:
            return {
                'tool': tool_name,
                'status': 'error',
                'error': str(e)
            }
            
    async def run_ruff(self, target: str) -> Dict:
        """Run Ruff linter (fast replacement for flake8, isort)."""
        if self.use_cache:
            cached = self.cache.get('ruff', target)
            if cached:
                print(f"✓ Using cached Ruff results for {target}")
                return cached
                
        cmd = ['ruff', 'check', target, '--output-format=json']
        result = await self.run_command_async(cmd, 'ruff')
        
        if result['status'] == 'success' and self.use_cache:
            self.cache.set('ruff', target, result)
            
        return result
        
    async def run_pylint(self, target: str) -> Dict:
        """Run Pylint analysis."""
        if self.use_cache:
            cached = self.cache.get('pylint', target)
            if cached:
                print(f"✓ Using cached Pylint results for {target}")
                return cached
                
        cmd = [
            'pylint',
            target,
            '--output-format=json',
            '--score=yes',
            '--persistent=yes',  # Use cache
        ]
        result = await self.run_command_async(cmd, 'pylint')
        
        if result['status'] == 'success' and self.use_cache:
            self.cache.set('pylint', target, result)
            
        return result
        
    async def run_bandit(self, target: str) -> Dict:
        """Run Bandit security scanner."""
        if self.use_cache:
            cached = self.cache.get('bandit', target)
            if cached:
                print(f"✓ Using cached Bandit results for {target}")
                return cached
                
        cmd = ['bandit', '-r', target, '-f', 'json', '-ll']
        result = await self.run_command_async(cmd, 'bandit')
        
        if result['status'] == 'success' and self.use_cache:
            self.cache.set('bandit', target, result)
            
        return result
        
    async def run_radon(self, target: str) -> Dict:
        """Run Radon complexity analysis."""
        if self.use_cache:
            cached = self.cache.get('radon', target)
            if cached:
                print(f"✓ Using cached Radon results for {target}")
                return cached
                
        # Run cyclomatic complexity
        cmd_cc = ['radon', 'cc', target, '-j', '--total-average']
        result_cc = await self.run_command_async(cmd_cc, 'radon_cc')
        
        # Run maintainability index
        cmd_mi = ['radon', 'mi', target, '-j']
        result_mi = await self.run_command_async(cmd_mi, 'radon_mi')
        
        result = {
            'tool': 'radon',
            'status': 'success' if result_cc['status'] == 'success' else 'failed',
            'cc': result_cc,
            'mi': result_mi,
        }
        
        if result['status'] == 'success' and self.use_cache:
            self.cache.set('radon', target, result)
            
        return result
        
    async def analyze_all(self) -> Dict:
        """Run all analysis tools in parallel."""
        targets = self.config.get('targets', ['.'])
        tools = self.config.get('tools', {})
        
        # Collect all tasks
        tasks = []
        
        for target in targets:
            if not os.path.exists(target):
                continue
                
            if tools.get('ruff', True):
                tasks.append(self.run_ruff(target))
            if tools.get('pylint', True):
                tasks.append(self.run_pylint(target))
            if tools.get('bandit', True):
                tasks.append(self.run_bandit(target))
            if tools.get('radon', True):
                tasks.append(self.run_radon(target))
                
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results
        organized = {
            'ruff': [],
            'pylint': [],
            'bandit': [],
            'radon': [],
        }
        
        for result in results:
            if isinstance(result, Exception):
                print(f"⚠️ Task failed: {result}")
                continue
            tool = result.get('tool', 'unknown')
            organized.setdefault(tool, []).append(result)
            
        return organized
        
    def save_results(self, results: Dict, output_file: str = 'analysis-results.json'):
        """Save results to file using fast JSON library."""
        try:
            with open(output_file, 'wb') as f:
                if USE_ORJSON:
                    # orjson is 3-5x faster
                    f.write(orjson.dumps(
                        results,
                        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
                    ))
                else:
                    json.dump(results, f, indent=2, sort_keys=True)
            print(f"✅ Results saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


async def main():
    """Main execution."""
    print("🚀 Starting optimized parallel code analysis...")
    print(f"📦 Using orjson: {USE_ORJSON}")
    
    analyzer = OptimizedCodeAnalyzer()
    
    # Clear old cache entries
    with timer("Cache cleanup"):
        analyzer.cache.clear_old(max_age_days=7)
    
    # Run analysis
    with timer("Total analysis"):
        results = await analyzer.analyze_all()
    
    # Save results
    analyzer.save_results(results)
    
    print("\n✅ Analysis complete!")


if __name__ == '__main__':
    asyncio.run(main())
