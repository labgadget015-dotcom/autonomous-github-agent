"""
Create all specialized agent files.
Run this after create_core_files.py
"""

from pathlib import Path

BASE_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")

# ============================================================================
# AGENT: Health Monitor
# ============================================================================

HEALTH_MONITOR_PY = '''"""Health monitoring agent for repository assessment."""

from typing import Any
from datetime import datetime, timedelta
from github.Repository import Repository
from autonomous_agent.core.base_agent import BaseAgent


class HealthMonitorAgent(BaseAgent):
    """Agent for monitoring repository health and metrics."""
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute health check on repository."""
        repo = self.github.get_repository(repository)
        
        health_report = {
            "repository": repository,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": await self._gather_metrics(repo),
            "issues": await self._identify_issues(repo),
            "recommendations": []
        }
        
        # Generate recommendations
        health_report["recommendations"] = self._generate_recommendations(health_report)
        
        # Log the health check
        self.log_action(
            action="health_check",
            repository=repository,
            details=health_report
        )
        
        return health_report
    
    async def _gather_metrics(self, repo: Repository) -> dict[str, Any]:
        """Gather repository metrics."""
        return {
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "watchers": repo.watchers_count,
            "size_kb": repo.size,
            "default_branch": repo.default_branch,
            "is_archived": repo.archived,
            "is_private": repo.private,
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_pages": repo.has_pages,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
        }
    
    async def _identify_issues(self, repo: Repository) -> dict[str, Any]:
        """Identify potential issues in the repository."""
        issues = {
            "stale_branches": [],
            "old_pull_requests": [],
            "security_alerts": [],
            "missing_files": [],
            "outdated_dependencies": []
        }
        
        # Check for stale branches
        branches = list(repo.get_branches())
        protected_branch = repo.default_branch
        
        for branch in branches:
            if branch.name == protected_branch:
                continue
            
            try:
                commit = branch.commit
                if commit.commit.author.date:
                    days_old = (datetime.utcnow() - commit.commit.author.date.replace(tzinfo=None)).days
                    if days_old > 90:
                        issues["stale_branches"].append({
                            "name": branch.name,
                            "days_old": days_old,
                            "last_commit": commit.commit.author.date.isoformat()
                        })
            except Exception:
                pass
        
        # Check for old PRs
        prs = self.github.get_pull_requests(repo, state="open")
        for pr in prs:
            days_old = (datetime.utcnow() - pr.created_at.replace(tzinfo=None)).days
            if days_old > 30:
                issues["old_pull_requests"].append({
                    "number": pr.number,
                    "title": pr.title,
                    "days_old": days_old,
                    "author": pr.user.login
                })
        
        # Check for missing essential files
        essential_files = ["README.md", "LICENSE", ".gitignore", "CONTRIBUTING.md"]
        try:
            contents = repo.get_contents("")
            existing_files = {item.name for item in contents if item.type == "file"}
            
            for essential in essential_files:
                if essential not in existing_files:
                    issues["missing_files"].append(essential)
        except Exception:
            pass
        
        return issues
    
    def _generate_recommendations(self, health_report: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        issues = health_report["issues"]
        
        if issues["stale_branches"]:
            count = len(issues["stale_branches"])
            recommendations.append(
                f"Delete {count} stale branch(es) not updated in 90+ days"
            )
        
        if issues["old_pull_requests"]:
            count = len(issues["old_pull_requests"])
            recommendations.append(
                f"Review or close {count} pull request(s) open for 30+ days"
            )
        
        if issues["missing_files"]:
            recommendations.append(
                f"Add missing files: {', '.join(issues['missing_files'])}"
            )
        
        if health_report["metrics"]["open_issues"] > 50:
            recommendations.append(
                "High number of open issues - consider triage and cleanup"
            )
        
        return recommendations
'''

# ============================================================================
# AGENT: Code Reviewer
# ============================================================================

CODE_REVIEWER_PY = '''"""Automated code review agent for pull requests."""

from typing import Any
from github.PullRequest import PullRequest
from autonomous_agent.core.base_agent import BaseAgent


class CodeReviewerAgent(BaseAgent):
    """Agent for automated PR code reviews."""
    
    async def execute(self, repository: str, pr_number: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Execute code review on PRs."""
        repo = self.github.get_repository(repository)
        
        if pr_number:
            prs = [repo.get_pull(pr_number)]
        else:
            prs = self.github.get_pull_requests(repo, state="open")
        
        results = []
        for pr in prs:
            review_result = await self._review_pr(repo, pr)
            results.append(review_result)
        
        return {
            "repository": repository,
            "reviewed_prs": len(results),
            "results": results
        }
    
    async def _review_pr(self, repo: Any, pr: PullRequest) -> dict[str, Any]:
        """Review a single pull request."""
        review = {
            "pr_number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "issues_found": [],
            "suggestions": [],
            "security_concerns": [],
            "score": 0
        }
        
        # Get PR files
        files = list(pr.get_files())
        
        for file in files:
            if file.patch is None:
                continue
            
            # Analyze with LLM
            analysis = await self._analyze_code_changes(file.filename, file.patch)
            
            if analysis.get("issues"):
                review["issues_found"].extend(analysis["issues"])
            
            if analysis.get("suggestions"):
                review["suggestions"].extend(analysis["suggestions"])
            
            if analysis.get("security_concerns"):
                review["security_concerns"].extend(analysis["security_concerns"])
        
        # Calculate score
        review["score"] = self._calculate_review_score(review)
        
        # Post review comment if issues found
        if review["issues_found"] or review["security_concerns"]:
            await self._post_review_comment(pr, review)
        
        # Log the review
        self.log_action(
            action="code_review",
            repository=f"{repo.owner.login}/{repo.name}",
            details=review
        )
        
        return review
    
    async def _analyze_code_changes(self, filename: str, patch: str) -> dict[str, Any]:
        """Analyze code changes using LLM."""
        prompt = f"""Review the following code changes in {filename}:

{patch}

Provide analysis in the following areas:
1. Code quality issues (syntax, style, best practices)
2. Security concerns (XSS, CSRF, SQL injection, secrets)
3. Performance issues
4. Suggestions for improvement

Return your analysis as structured feedback."""

        try:
            response = self.llm.complete(
                prompt=prompt,
                system="You are an expert code reviewer. Focus on actionable feedback."
            )
            
            # Parse LLM response (simplified - in production, use structured output)
            return {
                "issues": self._extract_issues(response),
                "suggestions": self._extract_suggestions(response),
                "security_concerns": self._extract_security(response)
            }
        except Exception as e:
            return {"issues": [], "suggestions": [], "security_concerns": []}
    
    def _extract_issues(self, response: str) -> list[str]:
        """Extract issues from LLM response."""
        # Simplified extraction - in production, use structured parsing
        issues = []
        for line in response.split("\\n"):
            if "issue" in line.lower() or "problem" in line.lower():
                issues.append(line.strip())
        return issues[:5]  # Limit to top 5
    
    def _extract_suggestions(self, response: str) -> list[str]:
        """Extract suggestions from LLM response."""
        suggestions = []
        for line in response.split("\\n"):
            if "suggest" in line.lower() or "recommend" in line.lower():
                suggestions.append(line.strip())
        return suggestions[:5]
    
    def _extract_security(self, response: str) -> list[str]:
        """Extract security concerns from LLM response."""
        concerns = []
        for line in response.split("\\n"):
            if "security" in line.lower() or "vulnerability" in line.lower():
                concerns.append(line.strip())
        return concerns
    
    def _calculate_review_score(self, review: dict[str, Any]) -> int:
        """Calculate a review score (0-100)."""
        score = 100
        score -= len(review["issues_found"]) * 5
        score -= len(review["security_concerns"]) * 15
        return max(0, score)
    
    async def _post_review_comment(self, pr: PullRequest, review: dict[str, Any]) -> None:
        """Post review comment on PR."""
        comment_parts = ["## 🤖 Automated Code Review\\n"]
        
        if review["security_concerns"]:
            comment_parts.append("### ⚠️ Security Concerns\\n")
            for concern in review["security_concerns"]:
                comment_parts.append(f"- {concern}\\n")
            comment_parts.append("\\n")
        
        if review["issues_found"]:
            comment_parts.append("### 🔍 Issues Found\\n")
            for issue in review["issues_found"][:5]:
                comment_parts.append(f"- {issue}\\n")
            comment_parts.append("\\n")
        
        if review["suggestions"]:
            comment_parts.append("### 💡 Suggestions\\n")
            for suggestion in review["suggestions"][:5]:
                comment_parts.append(f"- {suggestion}\\n")
        
        comment_parts.append(f"\\n**Review Score:** {review['score']}/100\\n")
        
        comment = "".join(comment_parts)
        self.github.create_issue_comment(pr, comment)
'''

# ============================================================================
# AGENT: Issue Manager
# ============================================================================

ISSUE_MANAGER_PY = '''"""Issue management and triage agent."""

from typing import Any
from github.Issue import Issue
from github.Repository import Repository
from autonomous_agent.core.base_agent import BaseAgent


class IssueManagerAgent(BaseAgent):
    """Agent for automated issue triage and management."""
    
    LABELS = {
        "bug": ["bug", "error", "crash", "broken", "fix"],
        "enhancement": ["feature", "enhancement", "improve", "add"],
        "documentation": ["docs", "documentation", "readme"],
        "security": ["security", "vulnerability", "cve"],
        "performance": ["performance", "slow", "optimization"],
        "question": ["question", "help", "how to"],
        "duplicate": ["duplicate", "already exists"],
    }
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute issue management tasks."""
        repo = self.github.get_repository(repository)
        issues = self.github.get_issues(repo, state="open")
        
        results = {
            "repository": repository,
            "processed": 0,
            "labeled": 0,
            "duplicates_found": 0,
            "auto_closed": 0
        }
        
        for issue in issues:
            if issue.pull_request:  # Skip PRs
                continue
            
            # Auto-label
            if not issue.labels:
                await self._auto_label_issue(issue)
                results["labeled"] += 1
            
            # Check for duplicates
            if await self._check_duplicate(repo, issue):
                results["duplicates_found"] += 1
            
            results["processed"] += 1
        
        self.log_action(
            action="issue_management",
            repository=repository,
            details=results
        )
        
        return results
    
    async def _auto_label_issue(self, issue: Issue) -> None:
        """Automatically label an issue based on content."""
        text = f"{issue.title} {issue.body or ''}".lower()
        
        labels_to_add = []
        
        for label, keywords in self.LABELS.items():
            if any(keyword in text for keyword in keywords):
                labels_to_add.append(label)
        
        if labels_to_add:
            try:
                issue.add_to_labels(*labels_to_add)
            except Exception:
                pass
    
    async def _check_duplicate(self, repo: Repository, issue: Issue) -> bool:
        """Check if issue is a duplicate using LLM."""
        # Get recent closed issues
        closed_issues = list(repo.get_issues(state="closed"))[:50]
        
        # Use LLM to detect duplicates
        prompt = f"""Is the following issue a duplicate of any previous issues?

New Issue:
Title: {issue.title}
Body: {issue.body or 'No description'}

Previous Issues:
"""
        for closed in closed_issues[:10]:
            prompt += f"- #{closed.number}: {closed.title}\\n"
        
        prompt += "\\nIf duplicate, respond with the issue number. Otherwise, respond 'NOT_DUPLICATE'."
        
        try:
            response = self.llm.complete(prompt)
            if "NOT_DUPLICATE" not in response and "#" in response:
                # Found duplicate - post comment
                dup_num = response.split("#")[1].split()[0]
                comment = f"This appears to be a duplicate of #{dup_num}. Please check if that issue addresses your concern."
                self.github.create_issue_comment(issue, comment)
                issue.add_to_labels("duplicate")
                return True
        except Exception:
            pass
        
        return False
'''

# ============================================================================
# AGENT: Branch Manager
# ============================================================================

BRANCH_MANAGER_PY = '''"""Branch management and cleanup agent."""

from typing import Any
from datetime import datetime, timedelta
from autonomous_agent.core.base_agent import BaseAgent


class BranchManagerAgent(BaseAgent):
    """Agent for automated branch operations."""
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute branch management tasks."""
        repo = self.github.get_repository(repository)
        
        results = {
            "repository": repository,
            "stale_branches_deleted": 0,
            "branches_analyzed": 0,
            "recommendations": []
        }
        
        branches = list(repo.get_branches())
        protected = repo.default_branch
        
        for branch in branches:
            if branch.name == protected:
                continue
            
            results["branches_analyzed"] += 1
            
            # Check if branch is stale
            try:
                commit = branch.commit
                if commit.commit.author.date:
                    days_old = (datetime.utcnow() - commit.commit.author.date.replace(tzinfo=None)).days
                    
                    if days_old > 180:  # 6 months
                        if self.requires_approval("branch_deletion"):
                            results["recommendations"].append(
                                f"Delete stale branch '{branch.name}' ({days_old} days old)"
                            )
                        else:
                            # Auto-delete if configured
                            if self.config.automation_level == "full-auto":
                                ref = repo.get_git_ref(f"heads/{branch.name}")
                                ref.delete()
                                results["stale_branches_deleted"] += 1
                                
                                self.log_action(
                                    action="branch_deletion",
                                    repository=repository,
                                    details={"branch": branch.name, "age_days": days_old},
                                    rollback={"type": "recreate_branch", "branch": branch.name, "sha": commit.sha}
                                )
            except Exception:
                pass
        
        return results
'''

# ============================================================================
# AGENT: Security Scanner
# ============================================================================

SECURITY_SCANNER_PY = '''"""Security scanning and vulnerability detection agent."""

import re
from typing import Any
from autonomous_agent.core.base_agent import BaseAgent


class SecurityScannerAgent(BaseAgent):
    """Agent for security scanning and vulnerability detection."""
    
    SECRET_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}",
        "Private Key": r"-----BEGIN (RSA |)PRIVATE KEY-----",
        "Generic Secret": r"(secret|password|api_key)\\s*=\\s*['\"][^'\"]+['\"]"
    }
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute security scan on repository."""
        repo = self.github.get_repository(repository)
        
        results = {
            "repository": repository,
            "secrets_found": [],
            "vulnerabilities": [],
            "recommendations": []
        }
        
        # Scan recent commits for secrets
        commits = list(repo.get_commits())[:50]
        
        for commit in commits:
            try:
                for file in commit.files:
                    if file.patch:
                        secrets = self._scan_for_secrets(file.filename, file.patch)
                        if secrets:
                            results["secrets_found"].extend(secrets)
            except Exception:
                continue
        
        # Check for security best practices
        results["recommendations"] = await self._check_security_practices(repo)
        
        self.log_action(
            action="security_scan",
            repository=repository,
            details=results
        )
        
        return results
    
    def _scan_for_secrets(self, filename: str, content: str) -> list[dict[str, Any]]:
        """Scan content for potential secrets."""
        findings = []
        
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": secret_type,
                    "file": filename,
                    "match": match.group()[:20] + "...",  # Truncate
                    "severity": "HIGH"
                })
        
        return findings
    
    async def _check_security_practices(self, repo: Any) -> list[str]:
        """Check for security best practices."""
        recommendations = []
        
        try:
            # Check for SECURITY.md
            try:
                repo.get_contents("SECURITY.md")
            except:
                recommendations.append("Add SECURITY.md with vulnerability reporting instructions")
            
            # Check for dependabot
            try:
                repo.get_contents(".github/dependabot.yml")
            except:
                recommendations.append("Enable Dependabot for automated dependency updates")
            
            # Check branch protection
            default_branch = repo.get_branch(repo.default_branch)
            if not default_branch.protected:
                recommendations.append("Enable branch protection on default branch")
        
        except Exception:
            pass
        
        return recommendations
'''

# ============================================================================
# AGENT: Workflow Optimizer
# ============================================================================

WORKFLOW_OPTIMIZER_PY = '''"""CI/CD workflow optimization agent."""

from typing import Any
from autonomous_agent.core.base_agent import BaseAgent


class WorkflowOptimizerAgent(BaseAgent):
    """Agent for CI/CD workflow analysis and optimization."""
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute workflow optimization."""
        repo = self.github.get_repository(repository)
        
        results = {
            "repository": repository,
            "workflows_analyzed": 0,
            "issues_found": [],
            "optimizations": []
        }
        
        try:
            # Get workflow files
            workflows_path = ".github/workflows"
            contents = repo.get_contents(workflows_path)
            
            for content in contents:
                if content.name.endswith((".yml", ".yaml")):
                    results["workflows_analyzed"] += 1
                    
                    workflow_content = content.decoded_content.decode()
                    analysis = await self._analyze_workflow(content.name, workflow_content)
                    
                    if analysis["issues"]:
                        results["issues_found"].extend(analysis["issues"])
                    if analysis["optimizations"]:
                        results["optimizations"].extend(analysis["optimizations"])
        
        except Exception:
            results["note"] = "No workflows found or unable to access"
        
        return results
    
    async def _analyze_workflow(self, filename: str, content: str) -> dict[str, Any]:
        """Analyze a workflow file."""
        issues = []
        optimizations = []
        
        # Check for common issues
        if "actions/checkout@v1" in content:
            issues.append(f"{filename}: Using outdated checkout action (v1)")
            optimizations.append(f"{filename}: Update to actions/checkout@v4")
        
        if "runs-on: ubuntu-latest" not in content and "runs-on: ubuntu" in content:
            optimizations.append(f"{filename}: Consider pinning Ubuntu version")
        
        # Use LLM for deeper analysis
        try:
            prompt = f"""Analyze this GitHub Actions workflow for optimization opportunities:

{content}

Identify:
1. Security issues
2. Performance improvements
3. Best practice violations"""

            response = self.llm.complete(prompt)
            # Parse response for additional insights
        except Exception:
            pass
        
        return {"issues": issues, "optimizations": optimizations}
'''

# ============================================================================
# AGENT: Documentation Generator
# ============================================================================

DOCUMENTATION_GENERATOR_PY = '''"""Documentation generation and maintenance agent."""

from typing import Any
from autonomous_agent.core.base_agent import BaseAgent


class DocumentationGeneratorAgent(BaseAgent):
    """Agent for automated documentation generation."""
    
    async def execute(self, repository: str, **kwargs: Any) -> dict[str, Any]:
        """Execute documentation tasks."""
        repo = self.github.get_repository(repository)
        
        results = {
            "repository": repository,
            "docs_updated": [],
            "suggestions": []
        }
        
        # Check README quality
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode()
            
            analysis = await self._analyze_readme(content)
            results["suggestions"].extend(analysis)
        except Exception:
            results["suggestions"].append("No README.md found - create one")
        
        return results
    
    async def _analyze_readme(self, content: str) -> list[str]:
        """Analyze README quality."""
        suggestions = []
        
        required_sections = ["Installation", "Usage", "Contributing", "License"]
        
        for section in required_sections:
            if section.lower() not in content.lower():
                suggestions.append(f"Add '{section}' section to README")
        
        if len(content) < 500:
            suggestions.append("README is too brief - add more details")
        
        if "```" not in content:
            suggestions.append("Add code examples to README")
        
        return suggestions
'''

# ============================================================================
# Write all agent files
# ============================================================================


def create_file(path: Path, content: str) -> None:
    """Create a file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ {path.relative_to(BASE_DIR)}")


def main():
    """Create all agent files."""
    print("Creating specialized agent files...\\n")

    files = {
        "autonomous_agent/agents/health_monitor.py": HEALTH_MONITOR_PY,
        "autonomous_agent/agents/code_reviewer.py": CODE_REVIEWER_PY,
        "autonomous_agent/agents/issue_manager.py": ISSUE_MANAGER_PY,
        "autonomous_agent/agents/branch_manager.py": BRANCH_MANAGER_PY,
        "autonomous_agent/agents/security_scanner.py": SECURITY_SCANNER_PY,
        "autonomous_agent/agents/workflow_optimizer.py": WORKFLOW_OPTIMIZER_PY,
        "autonomous_agent/agents/documentation_generator.py": DOCUMENTATION_GENERATOR_PY,
    }

    for file_path, content in files.items():
        create_file(BASE_DIR / file_path, content)

    print("\\n✅ All agents created successfully!")
    print("\\nNext: Run create_cli.py to build the CLI interface")


if __name__ == "__main__":
    main()
