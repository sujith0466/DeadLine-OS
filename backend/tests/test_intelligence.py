import pytest
from app import create_app
from config import TestingConfig
from models.intelligence import AccountabilityMetrics, CoachReport, ReflectionReport

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        from database.db import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_intelligence_models(app):
    """Test that the 3 intelligence models can be instantiated and saved."""
    from database.db import db
    
    with app.app_context():
        # Accountability
        metrics = AccountabilityMetrics(
            completion_rate=85,
            procrastination_score=15,
            key_findings=["Finding 1"]
        )
        db.session.add(metrics)
        
        # Coach
        coach = CoachReport(
            strengths=["Focus"],
            weekly_challenge="Do a thing"
        )
        db.session.add(coach)
        
        # Reflection
        refl = ReflectionReport(
            daily_summary="Good day"
        )
        db.session.add(refl)
        
        db.session.commit()
        
        assert AccountabilityMetrics.query.count() == 1
        assert CoachReport.query.count() == 1
        assert ReflectionReport.query.count() == 1
        
        saved_metrics = AccountabilityMetrics.query.first()
        assert saved_metrics.completion_rate == 85
        assert saved_metrics.key_findings == ["Finding 1"]
