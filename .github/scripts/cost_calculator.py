#!/usr/bin/env python3
"""
GitHub Actions Cost Calculator
Estimates costs for workflow runs based on runner usage and execution time.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CostCalculator:
    """Calculate GitHub Actions costs."""
    
    # GitHub Actions pricing (per minute)
    PRICING = {
        'ubuntu': 0.008,      # Ubuntu runners
        'windows': 0.016,     # Windows runners (2x Ubuntu)
        'macos': 0.08,        # macOS runners (10x Ubuntu)
        'ubuntu-large': 0.016,  # 4-core runners
        'ubuntu-xlarge': 0.032, # 8-core runners
    }
    
    # Free tier minutes per month
    FREE_TIER = {
        'free': 2000,
        'pro': 3000,
        'team': 10000,
        'enterprise': 50000,
    }
    
    def __init__(self):
        self.workflow_data = []
        self.account_type = os.getenv('GITHUB_ACCOUNT_TYPE', 'free').lower()
        
    def load_workflow_data(self, file_path: str = 'workflow-runs.json'):
        """Load workflow run data."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.workflow_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load workflow data: {e}")
            
    def calculate_run_cost(
        self,
        duration_seconds: int,
        runner_type: str = 'ubuntu',
        jobs_count: int = 1
    ) -> float:
        """Calculate cost for a single workflow run."""
        duration_minutes = duration_seconds / 60
        cost_per_minute = self.PRICING.get(runner_type, self.PRICING['ubuntu'])
        return duration_minutes * cost_per_minute * jobs_count
        
    def calculate_daily_cost(self, runs_per_day: int = 10) -> Dict[str, float]:
        """Estimate daily costs."""
        avg_duration = 300  # 5 minutes average
        single_run = self.calculate_run_cost(avg_duration)
        
        daily_cost = single_run * runs_per_day
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30
        annual_cost = daily_cost * 365
        
        return {
            'single_run': single_run,
            'daily': daily_cost,
            'weekly': weekly_cost,
            'monthly': monthly_cost,
            'annual': annual_cost,
        }
        
    def calculate_optimization_savings(
        self,
        old_duration: int,
        new_duration: int,
        runs_per_day: int = 10
    ) -> Dict[str, float]:
        """Calculate savings from optimization."""
        old_cost = self.calculate_run_cost(old_duration)
        new_cost = self.calculate_run_cost(new_duration)
        savings_per_run = old_cost - new_cost
        
        time_saved_minutes = (old_duration - new_duration) / 60
        
        return {
            'time_saved_per_run_minutes': time_saved_minutes,
            'cost_saved_per_run': savings_per_run,
            'daily_savings': savings_per_run * runs_per_day,
            'monthly_savings': savings_per_run * runs_per_day * 30,
            'annual_savings': savings_per_run * runs_per_day * 365,
            'percentage_improvement': ((old_duration - new_duration) / old_duration) * 100,
        }
        
    def check_free_tier_usage(
        self,
        monthly_minutes: float
    ) -> Dict[str, any]:
        """Check if usage exceeds free tier."""
        free_minutes = self.FREE_TIER.get(self.account_type, 0)
        overage_minutes = max(0, monthly_minutes - free_minutes)
        overage_cost = overage_minutes * self.PRICING['ubuntu']
        
        return {
            'free_tier_minutes': free_minutes,
            'used_minutes': monthly_minutes,
            'remaining_minutes': max(0, free_minutes - monthly_minutes),
            'overage_minutes': overage_minutes,
            'overage_cost': overage_cost,
            'within_free_tier': monthly_minutes <= free_minutes,
        }
        
    def generate_cost_report(
        self,
        runs_per_day: int = 10,
        avg_duration_seconds: int = 300
    ) -> str:
        """Generate comprehensive cost report."""
        costs = self.calculate_daily_cost(runs_per_day)
        monthly_minutes = (avg_duration_seconds / 60) * runs_per_day * 30
        tier_usage = self.check_free_tier_usage(monthly_minutes)
        
        report = f"""# GitHub Actions Cost Report
        
## Configuration
- **Account Type**: {self.account_type.title()}
- **Runs per Day**: {runs_per_day}
- **Average Duration**: {avg_duration_seconds}s ({avg_duration_seconds/60:.1f} min)
- **Runner Type**: ubuntu-latest

## Cost Breakdown

### Per-Run Costs
- Single run: ${costs['single_run']:.4f}

### Projected Costs
- **Daily**: ${costs['daily']:.2f}
- **Weekly**: ${costs['weekly']:.2f}
- **Monthly**: ${costs['monthly']:.2f}
- **Annual**: ${costs['annual']:.2f}

## Free Tier Analysis

### Monthly Minutes
- **Free Tier Allowance**: {tier_usage['free_tier_minutes']} minutes
- **Estimated Usage**: {tier_usage['used_minutes']:.0f} minutes
- **Remaining**: {tier_usage['remaining_minutes']:.0f} minutes

### Overage
"""
        
        if tier_usage['within_free_tier']:
            report += "✅ **Status**: Within free tier limits!\n"
        else:
            report += f"""⚠️ **Status**: Exceeds free tier
- **Overage Minutes**: {tier_usage['overage_minutes']:.0f} minutes
- **Overage Cost**: ${tier_usage['overage_cost']:.2f}/month
"""
        
        report += """
## Optimization Opportunities

### Current Optimizations
"""
        
        # Example optimization scenarios
        scenarios = [
            ('Parallel testing', 420, 300),
            ('Caching dependencies', 300, 180),
            ('Matrix build optimization', 180, 120),
        ]
        
        total_savings = 0
        for name, old, new in scenarios:
            savings = self.calculate_optimization_savings(old, new, runs_per_day)
            report += f"""
#### {name}
- Time saved: {savings['time_saved_per_run_minutes']:.1f} min/run
- Cost saved: ${savings['cost_saved_per_run']:.4f}/run
- Monthly savings: ${savings['monthly_savings']:.2f}
- Annual savings: ${savings['annual_savings']:.2f}
- Improvement: {savings['percentage_improvement']:.1f}%
"""
            total_savings += savings['annual_savings']
            
        report += f"""
### **Total Potential Annual Savings**: ${total_savings:.2f}

## Recommendations

"""
        
        recommendations = []
        
        if tier_usage['overage_minutes'] > 0:
            recommendations.append("🔴 **High Priority**: Reduce workflow runs to stay within free tier")
        
        if avg_duration_seconds > 300:
            recommendations.append("🟡 **Medium Priority**: Optimize workflow duration (currently above 5 min)")
            
        if runs_per_day > 20:
            recommendations.append("🟡 **Medium Priority**: Consider reducing test frequency or using smarter triggers")
            
        recommendations.extend([
            "🟢 **Best Practice**: Enable workflow caching for dependencies",
            "🟢 **Best Practice**: Use matrix builds for parallel testing",
            "🟢 **Best Practice**: Implement conditional job execution",
            "🟢 **Best Practice**: Use GitHub-hosted larger runners for critical paths only",
        ])
        
        for rec in recommendations:
            report += f"- {rec}\n"
            
        report += f"""
## Cost Reduction Strategies

### 1. Smart Triggers
```yaml
on:
  push:
    branches: [main]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  pull_request:
    types: [opened, synchronize]
```

### 2. Conditional Jobs
```yaml
jobs:
  expensive-job:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

### 3. Dependency Caching
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}
```

### 4. Fail Fast
```yaml
strategy:
  fail-fast: true
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

### 5. Parallel Execution
```yaml
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
```

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Next Review**: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
"""
        
        return report
        
    def save_report(self, report: str, file_path: str = 'cost-report.md'):
        """Save cost report to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Cost report saved to {file_path}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            
    def calculate_roi(
        self,
        setup_hours: float,
        hourly_rate: float,
        monthly_savings: float
    ) -> Dict[str, float]:
        """Calculate ROI for CI/CD optimization."""
        setup_cost = setup_hours * hourly_rate
        payback_months = setup_cost / monthly_savings if monthly_savings > 0 else float('inf')
        annual_roi = ((monthly_savings * 12 - setup_cost) / setup_cost) * 100 if setup_cost > 0 else 0
        
        return {
            'setup_cost': setup_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'payback_months': payback_months,
            'annual_roi_percentage': annual_roi,
            'break_even_date': (datetime.now() + timedelta(days=payback_months*30)).strftime('%Y-%m-%d'),
        }


def main():
    """Main execution."""
    calculator = CostCalculator()
    
    # Load environment variables
    runs_per_day = int(os.getenv('WORKFLOW_RUNS_PER_DAY', '10'))
    avg_duration = int(os.getenv('AVG_WORKFLOW_DURATION', '300'))
    
    print("🧮 Calculating GitHub Actions costs...")
    
    # Generate report
    report = calculator.generate_cost_report(runs_per_day, avg_duration)
    
    # Save report
    calculator.save_report(report, 'docs/COST_REPORT.md')
    
    # Calculate ROI
    setup_hours = float(os.getenv('SETUP_HOURS', '40'))
    hourly_rate = float(os.getenv('HOURLY_RATE', '100'))
    
    # Assume 30% cost reduction from optimizations
    current_monthly = calculator.calculate_daily_cost(runs_per_day)['monthly']
    optimized_monthly = current_monthly * 0.7
    monthly_savings = current_monthly - optimized_monthly
    
    roi = calculator.calculate_roi(setup_hours, hourly_rate, monthly_savings)
    
    print("\n📊 ROI Analysis:")
    print(f"- Setup Cost: ${roi['setup_cost']:.2f}")
    print(f"- Monthly Savings: ${roi['monthly_savings']:.2f}")
    print(f"- Annual Savings: ${roi['annual_savings']:.2f}")
    print(f"- Payback Period: {roi['payback_months']:.1f} months")
    print(f"- Annual ROI: {roi['annual_roi_percentage']:.1f}%")
    print(f"- Break Even: {roi['break_even_date']}")
    
    print("\n✅ Cost analysis complete!")


if __name__ == '__main__':
    main()
