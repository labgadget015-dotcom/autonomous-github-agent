"""Pytest configuration and fixtures for test suite."""
import pytest
import sys
import os
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / '.github' / 'scripts'))


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file():
    """Provide a temporary file for tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        yield f.name
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {
        'api_key': 'test_api_key',
        'model': 'test_model',
        'max_retries': 3,
        'timeout': 30,
        'debug': True
    }


@pytest.fixture
def mock_github_api():
    """Provide a mock GitHub API client."""
    mock_api = MagicMock()
    mock_api.get_repo.return_value = Mock()
    mock_api.create_issue.return_value = {'number': 1}
    return mock_api


@pytest.fixture
def sample_json_file(temp_directory):
    """Create a sample JSON file for testing."""
    file_path = os.path.join(temp_directory, 'test_config.json')
    test_data = {'key': 'value', 'number': 42}
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    return file_path


@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def error_scenarios():
    """Provide common error scenarios for testing."""
    return {
        'network_error': Exception('Network connection failed'),
        'api_error': Exception('API rate limit exceeded'),
        'validation_error': ValueError('Invalid input data'),
        'file_not_found': FileNotFoundError('File does not exist'),
        'permission_error': PermissionError('Access denied')
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_error_handler():
    """Provide a mock error handler."""
    handler = MagicMock()
    handler.handle_error = MagicMock(return_value=True)
    handler.errors = []
    return handler


@pytest.fixture
def sample_data_sets():
    """Provide sample data sets for testing."""
    return {
        'valid': {
            'string': 'test string',
            'number': 123,
            'list': [1, 2, 3],
            'dict': {'key': 'value'}
        },
        'invalid': {
            'none': None,
            'empty_string': '',
            'empty_list': [],
            'empty_dict': {}
        },
        'edge_cases': {
            'large_number': 10**10,
            'negative': -100,
            'special_chars': '!@#$%^&*()',
            'unicode': '你好世界🌍'
        }
    }


@pytest.fixture
def mock_file_system(temp_directory):
    """Create a mock file system structure."""
    structure = {
        'root': temp_directory,
        'files': [],
        'dirs': []
    }
    
    # Create some test files and directories
    test_dir = os.path.join(temp_directory, 'test_dir')
    os.makedirs(test_dir, exist_ok=True)
    structure['dirs'].append(test_dir)
    
    test_file = os.path.join(temp_directory, 'test_file.txt')
    with open(test_file, 'w') as f:
        f.write('test content')
    structure['files'].append(test_file)
    
    return structure


@pytest.fixture
def performance_metrics():
    """Provide performance metrics tracking."""
    return {
        'start_time': None,
        'end_time': None,
        'execution_time': 0,
        'operations': 0,
        'errors': 0
    }


# Pytest hooks for better test reporting
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test name
        if 'integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    logs = []
    
    def log_capture(message):
        logs.append(message)
    
    return {'logs': logs, 'capture': log_capture}


@pytest.fixture
def retry_config():
    """Provide retry configuration for tests."""
    return {
        'max_retries': 3,
        'retry_delay': 0.1,
        'backoff_factor': 2,
        'max_delay': 10
    }


@pytest.fixture
def security_test_data():
    """Provide security test data."""
    return {
        'sql_injection': ["'; DROP TABLE users; --", "1' OR '1'='1"],
        'xss': ['<script>alert("xss")</script>', '<img src=x onerror=alert(1)>'],
        'path_traversal': ['../../../etc/passwd', '..\\..\\..\\windows\\system32'],
        'command_injection': ['; ls -la', '| cat /etc/passwd']
    }


@pytest.fixture
def load_test_config():
    """Provide load testing configuration."""
    return {
        'concurrent_users': [1, 10, 50, 100],
        'request_rate': [1, 10, 100],
        'duration': 60,
        'ramp_up': 10
    }
