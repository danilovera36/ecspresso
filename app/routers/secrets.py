from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import App, Environment, Secret
from ..auth import get_current_user
from ..schemas import SecretCreate
from ..services.aws_client import SSMClient

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])

@router.post("/secrets")
def set_secret(payload: SecretCreate, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.name == payload.app_name).first()
    if not app: app = App(name=payload.app_name); db.add(app); db.commit(); db.refresh(app)
    env = db.query(Environment).filter(Environment.app_id == app.id, Environment.name == payload.environment).first()
    if not env: env = Environment(name=payload.environment, app_id=app.id); db.add(env); db.commit(); db.refresh(env)
    
    ssm_path = f"/ecspresso/{payload.app_name}/{payload.environment}/{payload.key}"
    
    # Check if Secret entry already exists in DB
    sec = db.query(Secret).filter(Secret.env_id == env.id, Secret.key == payload.key).first()
    
    try:
        # We always update the SSM parameter to ensure it has the latest value
        arn = SSMClient().put_parameter(ssm_path, payload.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AWS SSM Error: {str(e)}")
    
    if not sec:
        sec = Secret(key=payload.key, ssm_path=ssm_path, env_id=env.id)
        db.add(sec)
    
    db.commit()
    return {"status": "ok", "message": f"Secret {payload.key} saved to SSM.", "arn": arn}

@router.get("/secrets")
def list_secrets(app_name: str, environment: str, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.name == app_name).first()
    if not app: raise HTTPException(status_code=404, detail="App not found")
    env = db.query(Environment).filter(Environment.app_id == app.id, Environment.name == environment).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    secrets = db.query(Secret).filter(Secret.env_id == env.id).all()
    return [{"key": sec.key, "ssm_path": sec.ssm_path} for sec in secrets]
