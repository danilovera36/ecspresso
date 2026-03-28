from sqlalchemy.orm import Session
from . import models

def get_app_by_name(db: Session, name: str):
    return db.query(models.App).filter(models.App.name == name).first()

def create_app(db: Session, name: str):
    app = models.App(name=name)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

def get_environment(db: Session, app_id: int, name: str):
    return db.query(models.Environment).filter(models.Environment.app_id == app_id, models.Environment.name == name).first()

def create_environment(db: Session, app_id: int, name: str):
    env = models.Environment(name=name, app_id=app_id)
    db.add(env)
    db.commit()
    db.refresh(env)
    return env

def get_template(db: Session, env_id: int):
    return db.query(models.TaskDefinitionTemplate).filter(models.TaskDefinitionTemplate.env_id == env_id).first()

def get_variables(db: Session, env_id: int):
    return db.query(models.Variable).filter(models.Variable.env_id == env_id).all()

def get_secrets(db: Session, env_id: int):
    return db.query(models.Secret).filter(models.Secret.env_id == env_id).all()

def save_template(db: Session, env_id: int, target_container: str, base_json: dict):
    template = get_template(db, env_id)
    if template:
        template.base_json = base_json
        template.target_container = target_container
    else:
        template = models.TaskDefinitionTemplate(env_id=env_id, target_container=target_container, base_json=base_json)
        db.add(template)
    db.commit()
    return template
