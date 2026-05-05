#!/usr/bin/env python3
"""Enhanced Chain-of-Thought Template Selector with SKIP logic."""
from enum import Enum
from typing import Dict, Any, Set
import yaml
from pathlib import Path


class CoTTemplate(Enum):
    """Chain-of-Thought templates with SKIP option."""
    SKIP = "skip"  # No CoT needed - trivial changes
    ZERO_SHOT = "zero_shot"  # Simple, straightforward changes
    FEW_SHOT = "few_shot"  # Moderate complexity
    STEP_BACK = "step_back"  # High-level reasoning needed
    COMPOSITIONAL = "compositional"  # Complex, multi-step reasoning


class OptimizedCoTSelector:
    """Optimized CoT selector with skip logic for trivial changes."""
    
    # Documentation-only file patterns
    DOC_PATTERNS = {
        '.md', '.txt', '.rst', '.adoc',
        'README', 'LICENSE', 'CHANGELOG'
    }
    
    # Security-sensitive patterns
    SECURITY_PATTERNS = {
        'auth', 'password', 'secret', 'token', 'key',
        'security', 'crypto', 'encrypt', 'decrypt'
    }
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path(".github/config/policy.yml")
        self.config = self._load_config()
        
        # Optimized thresholds
        self.thresholds = {
            'skip_max_lines': 10,  # Skip CoT if ≤10 lines changed
            'zero_shot_max_lines': 50,
            'few_shot_max_lines': 200,
            'step_back_max_lines': 500
        }
    
    def _load_config(self) -> Dict:
        """Load configuration with fallback defaults."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        
        # Fallback defaults
        return {
            'ai_agent': {
                'cot_selection': {
                    'complexity_thresholds': {
                        'simple': 0.3,
                        'moderate': 0.6
                    }
                }
            }
        }
    
    def is_doc_only_change(self, context: Dict) -> bool:
        """Check if changes are documentation-only."""
        changed_files = context.get('changed_files', context.get('files', []))
        
        if not changed_files:
            return False
        
        for file in changed_files:
            if not file:
                continue
            
            file_lower = file.lower()
            # Check if file matches doc patterns
            is_doc = any(
                pattern in file_lower or file_lower.endswith(pattern)
                for pattern in self.DOC_PATTERNS
            )
            
            if not is_doc:
                return False
        
        return True
    
    def is_security_sensitive(self, context: Dict) -> bool:
        """Check if changes involve security-sensitive code."""
        changed_files = context.get('changed_files', context.get('files', []))
        
        for file in changed_files:
            if not file:
                continue
            
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in self.SECURITY_PATTERNS):
                return True
        
        return False
    
    def select_template(self, context: Dict) -> CoTTemplate:
        """Select optimal CoT template with SKIP logic."""
        lines_changed = context.get('lines_changed', 0)
        files_changed = context.get('files_changed', 0)
        
        # SKIP logic for trivial changes
        if self.is_doc_only_change(context):
            print("⏭️  SKIP: Documentation-only changes")
            return CoTTemplate.SKIP
        
        if lines_changed <= self.thresholds['skip_max_lines'] and files_changed <= 2:
            print("⏭️  SKIP: Trivial changes (≤10 lines, ≤2 files)")
            return CoTTemplate.SKIP
        
        # Security-sensitive changes always use COMPOSITIONAL
        if self.is_security_sensitive(context):
            print("🔒 SECURITY: Using COMPOSITIONAL for security-sensitive changes")
            return CoTTemplate.COMPOSITIONAL
        
        # Select based on complexity
        if lines_changed <= self.thresholds['zero_shot_max_lines']:
            print(f"✨ ZERO_SHOT: Simple change ({lines_changed} lines)")
            return CoTTemplate.ZERO_SHOT
        
        elif lines_changed <= self.thresholds['few_shot_max_lines']:
            print(f"📚 FEW_SHOT: Moderate complexity ({lines_changed} lines)")
            return CoTTemplate.FEW_SHOT
        
        elif lines_changed <= self.thresholds['step_back_max_lines']:
            print(f"🧠 STEP_BACK: High complexity ({lines_changed} lines)")
            return CoTTemplate.STEP_BACK
        
        else:
            print(f"🎯 COMPOSITIONAL: Very high complexity ({lines_changed} lines)")
            return CoTTemplate.COMPOSITIONAL
    
    def _analyze_complexity(self, context: Dict) -> float:
        """Analyze complexity score (0.0 to 1.0)."""
        score = 0.0
        
        # File-based scoring
        files_changed = context.get('files_changed', 0)
        if files_changed > 10:
            score += 0.3
        elif files_changed > 5:
            score += 0.15
        
        # Lines-based scoring
        lines_changed = context.get('lines_changed', 0)
        if lines_changed > 500:
            score += 0.3
        elif lines_changed > 200:
            score += 0.15
        
        # Security sensitivity
        if self.is_security_sensitive(context):
            score += 0.3
        
        # Labels-based scoring
        labels = str(context.get('labels', [])).lower()
        if 'breaking' in labels or 'major' in labels:
            score += 0.2
        
        return min(score, 1.0)
    
    def estimate_token_savings(self, template: CoTTemplate, baseline_tokens: int = 10000) -> Dict[str, Any]:
        """Estimate token savings for selected template."""
        savings_map = {
            CoTTemplate.SKIP: 0.95,  # 95% reduction
            CoTTemplate.ZERO_SHOT: 0.70,  # 70% reduction
            CoTTemplate.FEW_SHOT: 0.40,  # 40% reduction
            CoTTemplate.STEP_BACK: 0.20,  # 20% reduction
            CoTTemplate.COMPOSITIONAL: 0.0  # No reduction (full reasoning)
        }
        
        reduction = savings_map.get(template, 0.0)
        estimated_tokens = int(baseline_tokens * (1 - reduction))
        tokens_saved = baseline_tokens - estimated_tokens
        
        return {
            'template': template.value,
            'baseline_tokens': baseline_tokens,
            'estimated_tokens': estimated_tokens,
            'tokens_saved': tokens_saved,
            'reduction_percentage': reduction * 100
        }


if __name__ == "__main__":
    import json
    import sys
    
    # Example usage
    selector = OptimizedCoTSelector()
    
    # Test cases
    test_contexts = [
        {
            'name': 'Doc only',
            'files_changed': 2,
            'lines_changed': 15,
            'changed_files': ['README.md', 'docs/guide.md']
        },
        {
            'name': 'Trivial change',
            'files_changed': 1,
            'lines_changed': 5,
            'changed_files': ['src/utils.py']
        },
        {
            'name': 'Security change',
            'files_changed': 3,
            'lines_changed': 100,
            'changed_files': ['src/auth.py', 'src/security/tokens.py']
        },
        {
            'name': 'Large refactor',
            'files_changed': 15,
            'lines_changed': 800,
            'changed_files': ['src/core/*.py']
        }
    ]
    
    print("\n🎯 CoT Template Selection Examples:\n")
    for test in test_contexts:
        print(f"\n--- {test['name']} ---")
        template = selector.select_template(test)
        savings = selector.estimate_token_savings(template)
        print(f"Template: {template.value}")
        print(f"Token savings: {savings['tokens_saved']} ({savings['reduction_percentage']:.0f}%)")
        print(f"Estimated tokens: {savings['estimated_tokens']}")
    
    print("\n✅ CoT Selector test complete")
