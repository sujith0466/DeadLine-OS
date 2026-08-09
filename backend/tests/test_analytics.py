import pytest
from services.analytics_service import AnalyticsService
from datetime import date, datetime, timedelta, timezone

def test_get_productivity_heatmap(app, mocker):
    # We patch HabitLog and Task at the model level to avoid DB constraints
    mock_habit_query = mocker.patch("models.goal.HabitLog.query")
    mock_task_query = mocker.patch("models.task.Task.query")
    
    # We need to simulate the chaining: filter_by().filter().all()
    class MockHabitLog:
        def __init__(self, d):
            self.date = d
    
    class MockTask:
        def __init__(self, updated_at):
            self.updated_at = updated_at
    
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    mock_habit_query.filter_by.return_value.filter.return_value.all.return_value = [
        MockHabitLog(today.isoformat())
    ]
    
    mock_task_query.filter_by.return_value.filter.return_value.all.return_value = [
        MockTask(datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc))
    ]
    
    heatmap = AnalyticsService.get_productivity_heatmap("test-user")
    
    # Heatmap returns a list of dicts: [{"date": "...", "count": X, "level": Y}]
    today_entry = next((item for item in heatmap if item["date"] == today.isoformat()), None)
    yesterday_entry = next((item for item in heatmap if item["date"] == yesterday.isoformat()), None)
    
    assert today_entry is not None
    assert today_entry["count"] == 1
    assert yesterday_entry is not None
    assert yesterday_entry["count"] == 1


def test_generate_chief_of_staff_briefing_uses_gemini_wrapper(app, mocker):
    # Mock dependencies in get_overview
    mocker.patch("services.analytics_service.AnalyticsService.get_overview", return_value={
        "productivity_score": 80,
        "future_risk_forecast": "Low"
    })
    mocker.patch("models.task.Task.query")
    mocker.patch("models.intervention.Intervention.query")
    
    # Mock the Gemini service on the app extensions
    mock_gemini = mocker.Mock()
    mock_gemini.generate_text.return_value = "You are doing great."
    
    from flask import current_app
    current_app.extensions = getattr(current_app, "extensions", {})
    current_app.extensions["gemini_service"] = mock_gemini
    
    briefing = AnalyticsService.generate_chief_of_staff_briefing("test-user")
    assert "You are doing great." in briefing
    mock_gemini.generate_text.assert_called_once()
