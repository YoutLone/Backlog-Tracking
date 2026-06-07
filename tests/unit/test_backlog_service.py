import pytest
from uuid import uuid4
from app.services.backlog_service import BacklogService

class TestBacklogService:
    """Test backlog business logic."""
    
    def test_allowed_status_transitions(self):
        """Test status transition rules."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # Backlog starts by moving to todo.
        assert 'todo' in transitions['backlog']
        assert 'done' not in transitions['backlog']
        assert 'in_progress' not in transitions['backlog']
        assert 'review' not in transitions['backlog']
        
        # Todo can move forward or back.
        assert 'in_progress' in transitions['todo']
        assert 'backlog' in transitions['todo']
        assert 'done' not in transitions['todo']
        assert 'review' not in transitions['todo']
        
        # In progress can move to review or back to todo.
        assert 'review' in transitions['in_progress']
        assert 'todo' in transitions['in_progress']
        assert 'done' not in transitions['in_progress']
        assert 'backlog' not in transitions['in_progress']
        
        # Review can finish or go back to in progress.
        assert 'done' in transitions['review']
        assert 'in_progress' in transitions['review']
        assert 'backlog' not in transitions['review']
        assert 'todo' not in transitions['review']
        
        # Done items can be reopened.
        assert 'backlog' in transitions['done']
        assert 'todo' not in transitions['done']
        assert 'in_progress' not in transitions['done']
        assert 'review' not in transitions['done']
    
    def test_invalid_transition(self):
        """Test that invalid transitions are not allowed."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # No workflow shortcuts.
        assert 'in_progress' not in transitions['backlog']
        assert 'done' not in transitions['backlog']
        assert 'done' not in transitions['todo']
        assert 'done' not in transitions['in_progress']
        assert 'in_progress' not in transitions['done']
    
    def test_complete_workflow_path(self):
        """Test the complete valid workflow path."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        
        # Normal path: backlog -> todo -> in_progress -> review -> done.
        assert 'todo' in transitions['backlog']
        assert 'in_progress' in transitions['todo']
        assert 'review' in transitions['in_progress']
        assert 'done' in transitions['review']
        
        # Reopen path: done -> backlog.
        assert 'backlog' in transitions['done']
    
    def test_transition_dictionary_structure(self):
        """Test that all statuses have transition rules."""
        transitions = BacklogService.ALLOWED_TRANSITIONS
        expected_statuses = ['backlog', 'todo', 'in_progress', 'review', 'done']
        
        for status in expected_statuses:
            assert status in transitions, f"Missing transitions for {status}"
            assert isinstance(transitions[status], list), f"Transitions for {status} should be a list"
