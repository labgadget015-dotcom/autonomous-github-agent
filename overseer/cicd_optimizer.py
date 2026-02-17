#!/usr/bin/env python3
"""
CI/CD Optimizer Module

Designs and refines CI/CD workflows with automated testing, linting,
build, and deployment pipelines.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CICDOptimizer:
    """
    CI/CD workflow optimizer that analyzes and improves
    automated pipelines.
    """
    
    def __init__(self, repo_path: Path, config: Dict):
        self.repo_path = repo_path
        self.config = config
        self.workflows_dir = repo_path / '.github' / 'workflows'
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze CI/CD workflows and suggest improvements.
        
        Returns:
            Dictionary containing optimization recommendations
        """
        logger.info("Analyzing CI/CD workflows...")
        
        results = {
            'optimizations': [],
            'testing': [],
            'linting': [],
            'deployment': []
        }
        
        if not self.workflows_dir.exists():
            results['optimizations'].append({
                'type': 'missing_cicd',
                'severity': 'high',
                'recommendation': 'No CI/CD workflows found. Consider adding GitHub Actions workflows for automated testing and deployment.'
            })
            return results
        
        # Analyze existing workflows
        workflow_files = list(self.workflows_dir.glob('*.yml')) + list(self.workflows_dir.glob('*.yaml'))
        
        for workflow_file in workflow_files:
            self._analyze_workflow(workflow_file, results)
        
        # Check for missing workflows
        self._check_missing_workflows(results)
        
        logger.info(f"CI/CD analysis complete. Found {len(results['optimizations'])} optimization opportunities")
        
        return results
    
    def _analyze_workflow(self, workflow_file: Path, results: Dict):
        """Analyze a single workflow file"""
        try:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)
            
            if not workflow:
                return
            
            # Check for caching
            has_caching = self._check_for_caching(workflow)
            if not has_caching:
                results['optimizations'].append({
                    'type': 'missing_cache',
                    'file': workflow_file.name,
                    'severity': 'medium',
                    'recommendation': f'Workflow {workflow_file.name} could benefit from dependency caching to speed up builds.'
                })
            
            # Check for parallel execution
            has_matrix = self._check_for_matrix(workflow)
            if not has_matrix:
                results['optimizations'].append({
                    'type': 'no_matrix',
                    'file': workflow_file.name,
                    'severity': 'low',
                    'recommendation': f'Consider using matrix strategy in {workflow_file.name} for testing multiple versions.'
                })
            
            # Check for artifacts
            has_artifacts = self._check_for_artifacts(workflow)
            if not has_artifacts:
                results['optimizations'].append({
                    'type': 'no_artifacts',
                    'file': workflow_file.name,
                    'severity': 'low',
                    'recommendation': f'Consider uploading artifacts in {workflow_file.name} for debugging and analysis.'
                })
            
        except Exception as e:
            logger.warning(f"Error analyzing workflow {workflow_file}: {e}")
    
    def _check_for_caching(self, workflow: Dict) -> bool:
        """Check if workflow uses caching"""
        jobs = workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if step.get('uses', '').startswith('actions/cache'):
                    return True
        
        return False
    
    def _check_for_matrix(self, workflow: Dict) -> bool:
        """Check if workflow uses matrix strategy"""
        jobs = workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            if 'strategy' in job_config and 'matrix' in job_config['strategy']:
                return True
        
        return False
    
    def _check_for_artifacts(self, workflow: Dict) -> bool:
        """Check if workflow uploads artifacts"""
        jobs = workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if step.get('uses', '').startswith('actions/upload-artifact'):
                    return True
        
        return False
    
    def _check_missing_workflows(self, results: Dict):
        """Check for recommended workflows that are missing"""
        
        # Check for test workflow
        test_workflows = ['test.yml', 'tests.yml', 'ci.yml', 'test.yaml', 'tests.yaml', 'ci.yaml']
        has_test_workflow = any((self.workflows_dir / name).exists() for name in test_workflows)
        
        if not has_test_workflow:
            results['testing'].append({
                'type': 'missing_test_workflow',
                'severity': 'high',
                'recommendation': 'Add automated testing workflow to ensure code quality.'
            })
        
        # Check for linting workflow
        lint_workflows = ['lint.yml', 'linting.yml', 'quality.yml', 'lint.yaml', 'linting.yaml', 'quality.yaml']
        has_lint_workflow = any((self.workflows_dir / name).exists() for name in lint_workflows)
        
        if not has_lint_workflow:
            results['linting'].append({
                'type': 'missing_lint_workflow',
                'severity': 'medium',
                'recommendation': 'Add linting workflow to enforce code style and catch errors early.'
            })
        
        # Check for deployment workflow
        deploy_workflows = ['deploy.yml', 'deployment.yml', 'release.yml', 'deploy.yaml', 'deployment.yaml', 'release.yaml']
        has_deploy_workflow = any((self.workflows_dir / name).exists() for name in deploy_workflows)
        
        if not has_deploy_workflow:
            results['deployment'].append({
                'type': 'missing_deploy_workflow',
                'severity': 'low',
                'recommendation': 'Consider adding deployment workflow for automated releases.'
            })
