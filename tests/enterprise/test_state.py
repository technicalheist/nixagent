import os
import json
import pytest
import tempfile
from nixagent.state import StateManager

def test_state_basic_save_and_load():
    with tempfile.TemporaryDirectory() as tempdir:
        sm = StateManager(checkpoint_dir=tempdir, agent_name="TestAgent")
        
        test_messages = [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "Hello!"}
        ]
        test_extra = {"iteration": 5, "task": "greet"}
        
        # Save state
        saved_path = sm.save(test_messages, extra=test_extra)
        
        # Verify file existence
        assert os.path.exists(saved_path)
        assert os.path.basename(saved_path) == "checkpoint_0001.json"
        
        # Verify latest pointer exists
        latest_path = sm.latest_checkpoint_path()
        assert latest_path is not None
        assert os.path.exists(latest_path)
        
        # Load state and verify contents
        loaded_data = StateManager.load(latest_path)
        assert loaded_data["agent_name"] == "TestAgent"
        assert loaded_data["messages"] == test_messages
        assert loaded_data["extra"] == test_extra
        assert loaded_data["run_id"] == sm.run_id

def test_load_nonexistent_checkpoint():
    with pytest.raises(FileNotFoundError):
        StateManager.load("/path/that/definitely/does/not/exist.json")

def test_time_travel_multiple_saves():
    with tempfile.TemporaryDirectory() as tempdir:
        sm = StateManager(checkpoint_dir=tempdir, agent_name="TimeBot")
        
        msg1 = [{"role": "user", "content": "1"}]
        msg2 = [{"role": "user", "content": "2"}]
        
        # Save twice
        p1 = sm.save(msg1)
        p2 = sm.save(msg2)
        
        assert os.path.basename(p1) == "checkpoint_0001.json"
        assert os.path.basename(p2) == "checkpoint_0002.json"
        
        # Check we can load the old state (time travel)
        data1 = StateManager.load(p1)
        assert data1["messages"] == msg1
        
        # Check latest points to msg2
        data_latest = StateManager.load(sm.latest_checkpoint_path())
        assert data_latest["messages"] == msg2
