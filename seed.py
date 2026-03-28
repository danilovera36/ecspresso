import sys
import os
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, App, Environment, TaskDefinitionTemplate, Variable, Secret
from app.auth import get_password_hash

def seed_admin():
    db = SessionLocal()
    
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        print("Creating admin user...")
        hashed_password = get_password_hash("admin")
        admin_user = User(username="admin", hashed_password=hashed_password)
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully (User: admin / Pass: admin)")
    else:
        print("Admin user already exists.")
    
    db.close()

def seed_mock_data():
    db = SessionLocal()
    
    # Check if app exists
    demo_app = db.query(App).filter(App.name == "payment-service").first()
    if demo_app:
        print("Mock data already exists.")
        db.close()
        return

    print("Creating mock data (payment-service)...")
    app = App(name="payment-service")
    db.add(app)
    db.commit()
    db.refresh(app)

    env = Environment(name="development", app_id=app.id)
    db.add(env)
    db.commit()
    db.refresh(env)

    # Base TD template
    base_json = {
      "family": "payment-service-dev",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "payment-backend",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/payment:latest",
          "cpu": 256,
          "memory": 512,
          "essential": True,
          "portMappings": [{"containerPort": 8080, "hostPort": 8080}]
        }
      ]
    }
    
    template = TaskDefinitionTemplate(
        env_id=env.id,
        target_container="payment-backend",
        base_json=json.dumps(base_json)
    )
    db.add(template)

    # Variables Originales
    v1 = Variable(env_id=env.id, key="DB_HOST", value="postgres-dev.internal")
    v2 = Variable(env_id=env.id, key="DB_PORT", value="5432")
    v3 = Variable(env_id=env.id, key="NODE_ENV", value="development")
    db.add_all([v1, v2, v3])

    # Secreto de prueba original
    s1 = Secret(env_id=env.id, key="STRIPE_API_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/payment-service/development/STRIPE_API_KEY")
    db.add(s1)

    # --- NUEVA APP: auth-service ---
    print("Creating mock data (auth-service)...")
    app2 = App(name="auth-service")
    db.add(app2)
    db.commit()
    db.refresh(app2)

    env2_dev = Environment(name="development", app_id=app2.id)
    env2_prod = Environment(name="production", app_id=app2.id)
    db.add_all([env2_dev, env2_prod])
    db.commit()
    db.refresh(env2_dev)
    db.refresh(env2_prod)

    # Template para auth-service
    base_json_auth = {
      "family": "auth-service-dev",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "auth-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/auth:latest",
          "cpu": 512,
          "memory": 1024,
          "essential": True,
          "portMappings": [{"containerPort": 3000, "hostPort": 3000}]
        }
      ]
    }
    
    template2 = TaskDefinitionTemplate(
        env_id=env2_dev.id,
        target_container="auth-api",
        base_json=json.dumps(base_json_auth)
    )
    db.add(template2)

    # Variables y secretos de auth-service
    v_a1 = Variable(env_id=env2_dev.id, key="JWT_EXPIRE_HOURS", value="24")
    v_a2 = Variable(env_id=env2_dev.id, key="LOG_LEVEL", value="DEBUG")
    s_a1 = Secret(env_id=env2_dev.id, key="JWT_SECRET_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/auth-service/development/JWT_SECRET_KEY")
    db.add_all([v_a1, v_a2, s_a1])

    db.commit()
    db.close()
    print("Mock data created successfully!")

if __name__ == "__main__":
    seed_admin()
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        seed_mock_data()
