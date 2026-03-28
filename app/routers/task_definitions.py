from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import App, Environment, Variable, Secret, TaskDefinitionTemplate
from ..auth import get_current_user
from ..schemas import TemplateCreate
from ..services.td_merger import merge_td
from .. import crud

router = APIRouter(prefix="/api/v1/apps", dependencies=[Depends(get_current_user)])

@router.get("/")
def list_apps(db: Session = Depends(get_db)):
    apps = db.query(App).all()
    return [{"name": app.name} for app in apps]

@router.get("/{app_name}/td")
def get_generated_td(app_name: str, env: str, db: Session = Depends(get_db)):
    app = crud.get_app_by_name(db, app_name)
    if not app: raise HTTPException(status_code=404, detail="App not found")
    environment = crud.get_environment(db, app.id, env)
    if not environment: raise HTTPException(status_code=404, detail="Environment not found")
    template = crud.get_template(db, environment.id)
    if not template: raise HTTPException(status_code=404, detail="Template not found. Upload via UI.")
    variables = crud.get_variables(db, environment.id)
    secrets = crud.get_secrets(db, environment.id)
    return merge_td(template.base_json, template.target_container, variables, secrets)

@router.post("/{app_name}/td/template")
def save_td_template(app_name: str, payload: TemplateCreate, db: Session = Depends(get_db)):
    app = crud.get_app_by_name(db, app_name)
    if not app: app = crud.create_app(db, app_name)
    environment = crud.get_environment(db, app.id, payload.environment)
    if not environment: environment = crud.create_environment(db, app.id, payload.environment)
    crud.save_template(db, environment.id, payload.target_container, payload.base_json)
    return {"status": "ok", "message": "Template saved successfully."}
