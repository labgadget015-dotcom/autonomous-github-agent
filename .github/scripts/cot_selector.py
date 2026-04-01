#!/usr/bin/env python3
"""Chain-of-Thought Template Selector."""
from enum import Enum
from typing import Dict, Any
import yaml
from pathlib import Path

class CoTTemplate(Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    STEP_BACK = "step_back"
    COMPOSITIONAL = "compositional"

class CoTSelector:
    def __init__(self, config_path=None):
        self.config_path = config_path or Path(".github/config/policy.yml")
        self.config = self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except:
            return {'ai_agent': {'cot_selection': {'complexity_thresholds': {'simple': 0.3, 'moderate': 0.6}}}}
    
    def select_template(self, context: Dict) -> CoTTemplate:
        complexity = self._analyze_complexity(context)
        thresholds = self.config['ai_agent']['cot_selection']['complexity_thresholds']
        
        if complexity < thresholds['simple']:
            return CoTTemplate.ZERO_SHOT
        elif complexity < thresholds['moderate']:
            return CoTTemplate.FEW_SHOT
        else:
            return CoTTemplate.COMPOSITIONAL
    
    def _analyze_complexity(self, context: Dict) -> float:
        score = 0.0
        if context.get('files_changed', 0) > 10:
            score += 0.3
        if context.get('lines_changed', 0) > 500:
            score += 0.3
        if 'security' in str(context.get('labels', [])):
            score += 0.2
        return min(score, 1.0)
