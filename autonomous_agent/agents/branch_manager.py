"""Branch management and cleanup agent."""

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
