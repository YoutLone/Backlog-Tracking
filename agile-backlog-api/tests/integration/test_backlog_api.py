import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_backlog_item(
    client: AsyncClient, 
    test_user_token: str, 
    test_team
):
    """Test creating a backlog item."""
    response = await client.post(
        f"/api/backlog/teams/{test_team['id']}/items",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Backlog Item",
            "description": "This is a test item",
            "type": "story",
            "story_points": 5
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == "Test Backlog Item"
    assert data['type'] == "story"
    assert data['status'] == "backlog"
    assert data['story_points'] == 5
    assert 'id' in data

@pytest.mark.asyncio
async def test_list_backlog_items(
    client: AsyncClient,
    test_user_token: str,
    test_team
):
    """Test listing backlog items with pagination."""
    # Create a few items first
    for i in range(3):
        await client.post(
            f"/api/backlog/teams/{test_team['id']}/items",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "title": f"Item {i}",
                "type": "task",
                "story_points": 3
            }
        )
    
    # List items
    response = await client.get(
        f"/api/backlog/teams/{test_team['id']}/items?limit=10",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert data['total'] >= 3

@pytest.mark.asyncio
async def test_update_item_status(
    client: AsyncClient,
    test_user_token: str,
    test_team
):
    """Test updating item status with workflow validation."""
    # Create item
    create_resp = await client.post(
        f"/api/backlog/teams/{test_team['id']}/items",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Status Test Item",
            "type": "task"
        }
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()['id']
    
    # Update status to todo
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "todo"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'todo'

@pytest.mark.asyncio
async def test_update_item_status_to_in_progress(
    client: AsyncClient,
    test_user_token: str,
    test_team
):
    """Test updating item status through multiple states."""
    # Create item
    create_resp = await client.post(
        f"/api/backlog/teams/{test_team['id']}/items",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Multi Status Test",
            "type": "task"
        }
    )
    item_id = create_resp.json()['id']
    
    # backlog -> todo
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "todo"}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'todo'
    
    # todo -> in_progress
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'in_progress'
    
    # in_progress -> review
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "review"}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'review'
    
    # review -> done
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "done"}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'done'
    assert response.json()['completed_at'] is not None

@pytest.mark.asyncio
async def test_invalid_status_transition(
    client: AsyncClient,
    test_user_token: str,
    test_team
):
    """Test invalid status transition (backlog -> done should be rejected)."""
    # Create item
    create_resp = await client.post(
        f"/api/backlog/teams/{test_team['id']}/items",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Invalid Transition Test",
            "type": "task"
        }
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()['id']
    
    # Try invalid transition (backlog -> done is NOT allowed directly)
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "done"}
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()['detail']

@pytest.mark.asyncio
async def test_reopen_done_item(
    client: AsyncClient,
    test_user_token: str,
    test_team
):
    """Test reopening a done item."""
    # Create item
    create_resp = await client.post(
        f"/api/backlog/teams/{test_team['id']}/items",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Reopen Test",
            "type": "task"
        }
    )
    item_id = create_resp.json()['id']
    
    # Move to done through proper workflow
    for status in ['todo', 'in_progress', 'review', 'done']:
        response = await client.patch(
            f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"status": status}
        )
        assert response.status_code == 200
    
    # Verify it's done
    assert response.json()['status'] == 'done'
    assert response.json()['completed_at'] is not None
    
    # Reopen from done to backlog (allowed)
    response = await client.patch(
        f"/api/backlog/teams/{test_team['id']}/items/{item_id}/status",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"status": "backlog"}
    )
    
    assert response.status_code == 200
    assert response.json()['status'] == 'backlog'
    # completed_at should be null after reopening
    assert response.json()['completed_at'] is None