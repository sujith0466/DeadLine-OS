import uuid
from datetime import datetime, timezone
from enum import Enum
from database.db import db

class ScenarioType(str, Enum):
    DELAY_TASK = "DELAY_TASK"
    SKIP_TASK = "SKIP_TASK"
    ADD_TASK = "ADD_TASK"
    REDUCE_HOURS = "REDUCE_HOURS"
    INCREASE_WORKLOAD = "INCREASE_WORKLOAD"
    MOVE_DEADLINE = "MOVE_DEADLINE"
    EXECUTE_INTERVENTION = "EXECUTE_INTERVENTION"

class AgentExecutionLog(db.Model):
    __tablename__ = "agent_execution_logs"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_agentexecutionlog_user'), nullable=True, index=True)
    agent_name = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Integer, default=0)
    execution_time_ms = db.Column(db.Integer, default=0)
    metadata_payload = db.Column(db.JSON, nullable=True) # avoiding reserved keyword
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "status": self.status,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "metadata_payload": self.metadata_payload,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class TwinSimulationLog(db.Model):
    __tablename__ = "twin_simulation_logs"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_twinsimulationlog_user'), nullable=True, index=True)
    scenario_type = db.Column(db.String(50), nullable=False)
    
    current_success_probability = db.Column(db.Integer, nullable=True)
    projected_success_probability = db.Column(db.Integer, nullable=True)
    
    current_risk_score = db.Column(db.Integer, nullable=True)
    projected_risk_score = db.Column(db.Integer, nullable=True)
    
    capacity_impact = db.Column(db.Integer, nullable=True)
    schedule_stability = db.Column(db.Integer, nullable=True)
    
    scenario_payload = db.Column(db.JSON, nullable=False)
    simulation_result = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scenario_type": self.scenario_type,
            "current_success_probability": self.current_success_probability,
            "projected_success_probability": self.projected_success_probability,
            "current_risk_score": self.current_risk_score,
            "projected_risk_score": self.projected_risk_score,
            "capacity_impact": self.capacity_impact,
            "schedule_stability": self.schedule_stability,
            "scenario_payload": self.scenario_payload,
            "simulation_result": self.simulation_result,
            "created_at": self.created_at.isoformat()
        }

class OrchestratorEvent(db.Model):
    __tablename__ = "orchestrator_events"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_orchestratorevent_user'), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    agent = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    payload = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "payload": self.payload
        }
