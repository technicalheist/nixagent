import pytest
import requests
from unittest.mock import MagicMock
from nixagent.retry import call_with_retry, RetryError

def test_successful_call_no_retry():
    mock_fn = MagicMock(return_value="Success")
    result = call_with_retry(mock_fn, max_retries=3)
    
    assert result == "Success"
    mock_fn.assert_called_once()

def test_retryable_http_error():
    mock_fn = MagicMock()
    
    # Create a mock HTTP 429 error
    mock_response = MagicMock()
    mock_response.status_code = 429
    retry_err = requests.exceptions.HTTPError("Rate Limit", response=mock_response)
    
    # Fail twice, succeed on third try
    mock_fn.side_effect = [retry_err, retry_err, "Success"]
    
    # Use zero delay for fast testing
    result = call_with_retry(mock_fn, max_retries=3, retry_delay=0.0)
    
    assert result == "Success"
    assert mock_fn.call_count == 3

def test_fatal_http_error_no_retry():
    mock_fn = MagicMock()
    
    # Create a mock HTTP 401 error (fatal)
    mock_response = MagicMock()
    mock_response.status_code = 401
    fatal_err = requests.exceptions.HTTPError("Unauthorized", response=mock_response)
    
    mock_fn.side_effect = fatal_err
    
    with pytest.raises(requests.exceptions.HTTPError):
        call_with_retry(mock_fn, max_retries=3)
        
    # Should only be called once, no retries for 401
    mock_fn.assert_called_once()

def test_max_retries_exhausted():
    mock_fn = MagicMock()
    
    # Create a mock timeout error
    timeout_err = requests.exceptions.Timeout("Connection timed out")
    mock_fn.side_effect = timeout_err
    
    with pytest.raises(RetryError) as exc_info:
        # 1 initial call + 2 retries = 3 calls total
        call_with_retry(mock_fn, max_retries=2, retry_delay=0.0)
        
    assert mock_fn.call_count == 3
    assert "after 3 attempts" in str(exc_info.value)
