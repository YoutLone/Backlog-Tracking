import pytest
from uuid import uuid4
from app.services.backlog_service import BacklogService

class TestBacklogService:
    """Test backlog business logic."""
    
    def test_allowed_status_transitions(self):
        """Test status transition rules."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # Test backlog transitions
        # Backlog can only go to todo (not directly to done)
        assert 'todo' in transitions['backlog']
        assert 'done' not in transitions['backlog']  # ✅ Fixed: removed 'done' assertion
        assert 'in_progress' not in transitions['backlog']
        assert 'review' not in transitions['backlog']
        
        # Test todo transitions
        assert 'in_progress' in transitions['todo']
        assert 'backlog' in transitions['todo']
        assert 'done' not in transitions['todo']
        assert 'review' not in transitions['todo']
        
        # Test in_progress transitions
        assert 'review' in transitions['in_progress']
        assert 'todo' in transitions['in_progress']
        assert 'done' not in transitions['in_progress']
        assert 'backlog' not in transitions['in_progress']
        
        # Test review transitions
        assert 'done' in transitions['review']
        assert 'in_progress' in transitions['review']
        assert 'backlog' not in transitions['review']
        assert 'todo' not in transitions['review']
        
        # Test done can be reopened to backlog
        assert 'backlog' in transitions['done']
        assert 'todo' not in transitions['done']
        assert 'in_progress' not in transitions['done']
        assert 'review' not in transitions['done']
    
    def test_invalid_transition(self):
        """Test that invalid transitions are not allowed."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # Can't go from backlog directly to in_progress
        assert 'in_progress' not in transitions['backlog']
        
        # Can't go from backlog directly to done
        assert 'done' not in transitions['backlog']
        
        # Can't go from todo directly to done
        assert 'done' not in transitions['todo']
        
        # Can't go from in_progress directly to done
        assert 'done' not in transitions['in_progress']
        
        # Can't go from done to in_progress
        assert 'in_progress' not in transitions['done']
    
    def test_complete_workflow_path(self):
        """Test the complete valid workflow path."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # Valid workflow: backlog -> todo -> in_progress -> review -> done
        assert 'todo' in transitions['backlog']
        assert 'in_progress' in transitions['todo']
        assert 'review' in transitions['in_progress']
        assert 'done' in transitions['review']
        
        # Reopen workflow: done -> backlog
        assert 'backlog' in transitions['done']
    
    def test_transition_dictionary_structure(self):
        """Test that all statuses have transition rules."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        expected_statuses = ['backlog', 'todo', 'in_progress', 'review', 'done']
        
        for status in expected_statuses:
            assert status in transitions, f"Missing transitions for {status}"
            assert isinstance(transitions[status], list), f"Transitions for {status} should be a list"