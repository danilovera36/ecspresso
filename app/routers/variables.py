from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import App, Environment, Variable
from ..auth import get_current_user
from ..schemas import VariableCreate

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])

@router.post("/variables")
def set_variable(payload: VariableCreate, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.name == payload.app_name).first()
    if not app: app = App(name=payload.app_name); db.add(app); db.commit(); db.refresh(app)
    env = db.query(Environment).filter(Environment.app_id == app.id, Environment.name == payload.environment).first()
    if not env: env = Environment(name=payload.environment, app_id=app.id); db.add(env); db.commit(); db.refresh(env)
    var = db.query(Variable).filter(Variable.env_id == env.id, Variable.key == payload.key).first()
    if var: var.value = payload.value
    else: var = Variable(key=payload.key, value=payload.value, env_id=env.id); db.add(var)
    db.commit()
    return {"status": "ok", "message": f"Variable {payload.key} saved."}
