"""
Tests for core infrastructure modules.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import tempfile
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_base import BaseAgent
from core.github_client import GitHubClient
from core.llm_provider import LLMClient
from core.audit_logger import AuditLogger
from core.policy_engine import PolicyEngine
from core.message_queue import MessageQueue


# Fixtures for core tests
@pytest.fixture
def core_config():
    """Configuration for core components"""
    return {
        'github_token': 'test_token',
        'openai_api_key': 'test_openai_key',
        'anthropic_api_key': 'test_anthropic_key',
        'llm_provider': 'openai',
        'model': 'gpt-4',
        'audit_log_path': 'logs/test_audit.jsonl',
        'policy_file': 'config/policies.yaml',
        'redis_host': 'localhost',
        'redis_port': 6379
    }


@pytest.fixture
def mock_github_client():
    """Mock GitHub client"""
    with patch('core.github_client.Github') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def temp_audit_log():
    """Temporary audit log file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


# Test Agent Base
class TestAgentBase:
    """Test BaseAgent class"""
    
    class TestAgent(BaseAgent):
        """Concrete test agent"""
        
        def get_supported_actions(self):
            return ['test_action']
        
        async def _execute(self, task):
            action = task.get('action')
            if action == 'test_action':
                return {'result': 'success'}
            raise ValueError(f"Unknown action: {action}")
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, core_config):
        """Test agent initialization"""
        agent = self.TestAgent('test_agent', core_config)
        
        assert agent.name == 'test_agent'
        assert agent.config == core_config
        assert agent._initialized is True
    
    @pytest.mark.asyncio
    async def test_execute_lifecycle(self, core_config):
        """Test full execution lifecycle"""
        agent = self.TestAgent('test_agent', core_config)
        
        task = {
            'id': 'task_123',
            'action': 'test_action',
            'params': {}
        }
        
        with patch.object(agent.policy, 'check_action', return_value={'requires_approval': False}):
            with patch.object(agent.audit, 'log_action', return_value=None):
                result = await agent.execute(task)
        
        assert result['status'] == 'success'
        assert result['task_id'] == 'task_123'
        assert result['agent'] == 'test_agent'
    
    @pytest.mark.asyncio
    async def test_execute_with_approval(self, core_config):
        """Test execution requiring approval"""
        agent = self.TestAgent('test_agent', core_config)
        
        task = {
            'id': 'task_456',
            'action': 'test_action',
            'params': {}
        }
        
        with patch.object(agent.policy, 'check_action', return_value={
            'requires_approval': True,
            'reason': 'Test approval required'
        }):
            result = await agent.execute(task)
        
        assert result['status'] == 'pending_approval'
        assert 'approval_reason' in result
    
    @pytest.mark.asyncio
    async def test_validation_failure(self, core_config):
        """Test task validation failure"""
        agent = self.TestAgent('test_agent', core_config)
        
        task = {}  # Missing required 'action' field
        
        result = await agent.execute(task)
        
        assert result['status'] == 'error'
        assert 'validation failed' in result['error'].lower()
    
    def test_get_capabilities(self, core_config):
        """Test getting agent capabilities"""
        agent = self.TestAgent('test_agent', core_config)
        
        capabilities = agent.get_capabilities()
        
        assert capabilities['name'] == 'test_agent'
        assert 'test_action' in capabilities['actions']


# Test GitHub Client
class TestGitHubClient:
    """Test GitHubClient class"""
    
    def test_initialization(self, core_config, mock_github_client):
        """Test GitHub client initialization"""
        client = GitHubClient(core_config)
        
        assert client.config == core_config
        assert client._min_request_interval == 0.1
    
    def test_rate_limit_check(self, core_config, mock_github_client):
        """Test rate limit checking"""
        mock_rate_limit = MagicMock()
        mock_rate_limit.core.limit = 5000
        mock_rate_limit.core.remaining = 4500
        mock_github_client.get_rate_limit.return_value = mock_rate_limit
        
        client = GitHubClient(core_config)
        rate_limit_info = client.check_rate_limit()
        
        assert rate_limit_info['limit'] == 5000
        assert rate_limit_info['remaining'] == 4500
        assert rate_limit_info['used'] == 500
    
    def test_create_issue(self, core_config, mock_github_client):
        """Test issue creation"""
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_repo.create_issue.return_value = mock_issue
        mock_github_client.get_repo.return_value = mock_repo
        
        client = GitHubClient(core_config)
        issue = client.create_issue('owner', 'repo', 'Test Issue', 'Body')
        
        assert issue.number == 123
        mock_repo.create_issue.assert_called_once()


# Test LLM Provider
class TestLLMProvider:
    """Test LLMProvider class"""
    
    def test_initialization_openai(self, core_config):
        """Test OpenAI provider initialization"""
        config = core_config.copy()
        config['llm_provider'] = 'openai'
        
        with patch('openai.OpenAI') as mock_openai:
            client = LLMClient(config)
            
            assert client.provider == 'openai'
            assert client.model == 'gpt-4'
            mock_openai.assert_called_once()
    
    def test_initialization_anthropic(self, core_config):
        """Test Anthropic provider initialization"""
        config = core_config.copy()
        config['llm_provider'] = 'anthropic'
        config['model'] = 'claude-3-opus-20240229'
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            client = LLMClient(config)
            
            assert client.provider == 'anthropic'
            assert client.model == 'claude-3-opus-20240229'
            mock_anthropic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_openai(self, core_config):
        """Test text generation with OpenAI"""
        config = core_config.copy()
        config['llm_provider'] = 'openai'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = LLMClient(config)
            result = await client.generate("Test prompt")
            
            assert result['content'] == "Generated text"
            assert result['usage']['total_tokens'] == 30
    
    def test_token_usage_tracking(self, core_config):
        """Test token usage tracking"""
        with patch('openai.OpenAI'):
            client = LLMClient(core_config)
            
            assert client.get_token_usage() == 0
            
            client.total_tokens = 100
            assert client.get_token_usage() == 100
            
            client.reset_token_usage()
            assert client.get_token_usage() == 0


# Test Audit Logger
class TestAuditLogger:
    """Test AuditLogger class"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_audit_log):
        """Test audit logger initialization"""
        config = {'audit_log_path': temp_audit_log}
        logger = AuditLogger(config)
        
        assert logger.log_file == Path(temp_audit_log)
        assert logger.log_file.parent.exists()
    
    @pytest.mark.asyncio
    async def test_log_action(self, temp_audit_log):
        """Test logging an action"""
        config = {'audit_log_path': temp_audit_log}
        logger = AuditLogger(config)
        
        await logger.log_action(
            agent='test_agent',
            action='test_action',
            params={'key': 'value'},
            result={'status': 'ok'},
            task_id='task_123',
            status='success'
        )
        
        # Read log file
        with open(temp_audit_log, 'r') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['agent'] == 'test_agent'
        assert log_entry['action'] == 'test_action'
        assert log_entry['task_id'] == 'task_123'
        assert log_entry['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_get_logs(self, temp_audit_log):
        """Test retrieving logs"""
        config = {'audit_log_path': temp_audit_log}
        logger = AuditLogger(config)
        
        # Log multiple actions
        for i in range(3):
            await logger.log_action(
                agent=f'agent_{i}',
                action='test_action',
                params={},
                result={},
                task_id=f'task_{i}',
                status='success'
            )
        
        logs = logger.get_logs()
        assert len(logs) == 3
        
        # Filter by agent
        agent_logs = logger.get_logs(agent='agent_1')
        assert len(agent_logs) == 1
        assert agent_logs[0]['agent'] == 'agent_1'
    
    def test_rollback_instructions(self, temp_audit_log):
        """Test rollback instruction generation"""
        config = {'audit_log_path': temp_audit_log}
        logger = AuditLogger(config)
        
        rollback = logger._generate_rollback_instructions(
            'create_issue',
            {},
            {}
        )
        
        assert 'close' in rollback.lower() or 'issue' in rollback.lower()


# Test Policy Engine
class TestPolicyEngine:
    """Test PolicyEngine class"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test policy engine initialization"""
        config = {}
        engine = PolicyEngine(config)
        
        assert 'requires_approval' in engine.policies
        assert 'auto_approved' in engine.policies
    
    @pytest.mark.asyncio
    async def test_auto_approved_action(self):
        """Test auto-approved action"""
        config = {}
        engine = PolicyEngine(config)
        
        result = await engine.check_action('label_issue', {})
        
        assert result['requires_approval'] is False
    
    @pytest.mark.asyncio
    async def test_requires_approval_action(self):
        """Test action requiring approval"""
        config = {}
        engine = PolicyEngine(config)
        
        result = await engine.check_action('delete_main_branch', {})
        
        assert result['requires_approval'] is True
        assert 'reason' in result
    
    @pytest.mark.asyncio
    async def test_destructive_action_detection(self):
        """Test destructive action detection"""
        config = {}
        engine = PolicyEngine(config)
        
        # Test with destructive keyword
        result = await engine.check_action('custom_delete_action', {})
        assert result['requires_approval'] is True
        
        # Test with protected branch
        result = await engine.check_action('merge', {'branch': 'main'})
        assert result['requires_approval'] is True
    
    def test_add_approval_rule(self):
        """Test adding approval rule"""
        config = {}
        engine = PolicyEngine(config)
        
        engine.add_approval_rule('new_action')
        
        assert 'new_action' in engine.policies['requires_approval']
    
    def test_remove_approval_rule(self):
        """Test removing approval rule"""
        config = {}
        engine = PolicyEngine(config)
        
        engine.add_approval_rule('temp_action')
        engine.remove_approval_rule('temp_action')
        
        assert 'temp_action' not in engine.policies['requires_approval']


# Test Message Queue
class TestMessageQueue:
    """Test MessageQueue class"""
    
    def test_initialization_without_redis(self):
        """Test initialization without Redis"""
        config = {'redis_host': 'nonexistent'}
        queue = MessageQueue(config)
        
        # Should fall back to in-memory queue
        assert hasattr(queue, '_in_memory_queue')
    
    @pytest.mark.asyncio
    async def test_enqueue_dequeue_memory(self):
        """Test enqueue/dequeue with in-memory queue"""
        config = {'redis_host': 'nonexistent'}
        queue = MessageQueue(config)
        
        task = {'type': 'test', 'data': 'value'}
        
        await queue.enqueue('test_queue', task, priority=1)
        
        dequeued = await queue.dequeue('test_queue')
        
        assert dequeued == task
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test priority-based ordering"""
        config = {'redis_host': 'nonexistent'}
        queue = MessageQueue(config)
        
        # Enqueue with different priorities
        await queue.enqueue('test_queue', {'id': 1}, priority=1)
        await queue.enqueue('test_queue', {'id': 2}, priority=5)
        await queue.enqueue('test_queue', {'id': 3}, priority=3)
        
        # Should dequeue in priority order (highest first)
        first = await queue.dequeue('test_queue')
        assert first['id'] == 2  # Priority 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
