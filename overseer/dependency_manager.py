#!/usr/bin/env python3
"""
Dependency Manager Module

Smart dependency management with vulnerability detection
and upgrade recommendations.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DependencyManager:
    """
    Intelligent dependency manager that detects outdated packages,
    vulnerabilities, and suggests secure upgrades.
    """
    
    def __init__(self, repo_path: Path, config: Dict):
        self.repo_path = repo_path
        self.config = config
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze dependencies for issues and recommendations.
        
        Returns:
            Dictionary containing dependency analysis
        """
        logger.info("Analyzing dependencies...")
        
        results = {
            'outdated': [],
            'vulnerabilities': [],
            'patches': [],
            'recommendations': []
        }
        
        # Check for Python dependencies
        requirements_file = self.repo_path / 'requirements.txt'
        if requirements_file.exists():
            python_results = self._analyze_python_dependencies(requirements_file)
            results['outdated'].extend(python_results['outdated'])
            results['vulnerabilities'].extend(python_results['vulnerabilities'])
            results['recommendations'].extend(python_results['recommendations'])
        
        # Check for JavaScript dependencies
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            js_results = self._analyze_javascript_dependencies(package_json)
            results['outdated'].extend(js_results['outdated'])
            results['vulnerabilities'].extend(js_results['vulnerabilities'])
            results['recommendations'].extend(js_results['recommendations'])
        
        logger.info(f"Found {len(results['vulnerabilities'])} vulnerabilities, {len(results['outdated'])} outdated packages")
        
        return results
    
    def _analyze_python_dependencies(self, requirements_file: Path) -> Dict[str, List]:
        """Analyze Python dependencies from requirements.txt"""
        results = {
            'outdated': [],
            'vulnerabilities': [],
            'recommendations': []
        }
        
        # Parse requirements
        dependencies = self._parse_requirements(requirements_file)
        
        # Check each dependency
        for dep in dependencies:
            # Check if version is pinned
            if not dep.get('version'):
                results['recommendations'].append({
                    'package': dep['name'],
                    'type': 'version_pinning',
                    'severity': 'low',
                    'message': f"Package {dep['name']} should have a pinned version for reproducibility."
                })
            
            # Check for known vulnerabilities (simplified - would use safety/pip-audit in production)
            vulnerability = self._check_vulnerability(dep['name'], dep.get('version'))
            if vulnerability:
                results['vulnerabilities'].append(vulnerability)
                
                # Add recommendation to upgrade
                results['recommendations'].append({
                    'package': dep['name'],
                    'type': 'security_upgrade',
                    'severity': 'high',
                    'current_version': dep.get('version'),
                    'recommended_version': vulnerability.get('fixed_in'),
                    'message': f"Upgrade {dep['name']} to fix security vulnerability: {vulnerability['description']}"
                })
        
        return results
    
    def _analyze_javascript_dependencies(self, package_json: Path) -> Dict[str, List]:
        """Analyze JavaScript dependencies from package.json"""
        results = {
            'outdated': [],
            'vulnerabilities': [],
            'recommendations': []
        }
        
        try:
            with open(package_json) as f:
                data = json.load(f)
            
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            
            all_deps = {**dependencies, **dev_dependencies}
            
            for name, version in all_deps.items():
                # Check for ^ or ~ version ranges
                if version.startswith('^') or version.startswith('~'):
                    results['recommendations'].append({
                        'package': name,
                        'type': 'version_range',
                        'severity': 'low',
                        'message': f"Package {name} uses version range {version}. Consider pinning for consistency."
                    })
        
        except Exception as e:
            logger.warning(f"Error analyzing package.json: {e}")
        
        return results
    
    def _parse_requirements(self, requirements_file: Path) -> List[Dict]:
        """Parse requirements.txt file"""
        dependencies = []
        
        try:
            with open(requirements_file) as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse package and version
                    match = re.match(r'([a-zA-Z0-9\-_]+)([>=<~!]+)?([\d.]+)?', line)
                    if match:
                        name = match.group(1)
                        operator = match.group(2)
                        version = match.group(3)
                        
                        dependencies.append({
                            'name': name,
                            'operator': operator,
                            'version': version,
                            'raw': line
                        })
        
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt: {e}")
        
        return dependencies
    
    def _check_vulnerability(self, package: str, version: Optional[str]) -> Optional[Dict]:
        """
        Check if a package has known vulnerabilities.
        
        This is a simplified implementation. In production, this would:
        - Query safety database
        - Check GitHub Advisory Database
        - Use pip-audit or similar tools
        """
        # Known vulnerable packages (simplified example)
        known_vulns = {
            'urllib3': {
                'version': '1.26.4',
                'operator': '<',
                'description': 'SSRF vulnerability in urllib3',
                'fixed_in': '1.26.5',
                'severity': 'high'
            },
            'requests': {
                'version': '2.25.0',
                'operator': '<',
                'description': 'Potential security issue',
                'fixed_in': '2.25.1',
                'severity': 'medium'
            }
        }
        
        if package in known_vulns:
            vuln = known_vulns[package]
            
            # Simple version comparison
            if version and self._is_vulnerable_version(version, vuln['version'], vuln['operator']):
                return {
                    'package': package,
                    'version': version,
                    'description': vuln['description'],
                    'severity': vuln['severity'],
                    'fixed_in': vuln['fixed_in']
                }
        
        return None
    
    def _is_vulnerable_version(self, current: str, vuln_version: str, operator: str) -> bool:
        """Compare versions to check if vulnerable"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            vuln_parts = [int(x) for x in vuln_version.split('.')]
            
            # Pad to same length
            max_len = max(len(current_parts), len(vuln_parts))
            current_parts += [0] * (max_len - len(current_parts))
            vuln_parts += [0] * (max_len - len(vuln_parts))
            
            if operator == '<':
                return current_parts < vuln_parts
            elif operator == '<=':
                return current_parts <= vuln_parts
            elif operator == '==':
                return current_parts == vuln_parts
            
        except Exception:
            pass
        
        return False
