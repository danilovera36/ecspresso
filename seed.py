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

def seed_mock_data(force=False):
    db = SessionLocal()
    
    # Check if extensive mock data already exists
    user_service = db.query(App).filter(App.name == "user-service").first()
    if user_service and not force:
        print("Extensive mock data already exists.")
        db.close()
        return
    
    # If force is True, delete existing mock data
    if force:
        print("Force flag detected. Deleting existing mock data...")
        # Delete in reverse order of dependencies
        db.query(Secret).delete()
        db.query(Variable).delete()
        db.query(TaskDefinitionTemplate).delete()
        db.query(Environment).delete()
        db.query(App).delete()
        db.commit()
        print("Existing mock data deleted.")

    print("Creating extensive mock data...")
    
    # 1. Payment Service (existing)
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
          "portMappings": [{"containerPort": 8080, "hostPort": 8080}],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/payment-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
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

    # --- AUTH SERVICE ---
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
          "portMappings": [{"containerPort": 3000, "hostPort": 3000}],
          "environment": [
            {"name": "PORT", "value": "3000"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/auth-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
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

    # Production environment for auth-service
    base_json_auth_prod = {
      "family": "auth-service-prod",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "auth-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/auth:latest",
          "cpu": 1024,
          "memory": 2048,
          "essential": True,
          "portMappings": [{"containerPort": 3000, "hostPort": 3000}],
          "environment": [
            {"name": "PORT", "value": "3000"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/auth-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template2_prod = TaskDefinitionTemplate(
        env_id=env2_prod.id,
        target_container="auth-api",
        base_json=json.dumps(base_json_auth_prod)
    )
    db.add(template2_prod)
    
    v_a3 = Variable(env_id=env2_prod.id, key="JWT_EXPIRE_HOURS", value="168")  # 7 days
    v_a4 = Variable(env_id=env2_prod.id, key="LOG_LEVEL", value="INFO")
    v_a5 = Variable(env_id=env2_prod.id, key="ENABLE_DEBUG_ENDPOINTS", value="false")
    s_a2 = Secret(env_id=env2_prod.id, key="JWT_SECRET_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/auth-service/production/JWT_SECRET_KEY")
    s_a3 = Secret(env_id=env2_prod.id, key="ADMIN_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/auth-service/production/ADMIN_PASSWORD")
    db.add_all([v_a3, v_a4, v_a5, s_a2, s_a3])

    # --- USER SERVICE ---
    print("Creating mock data (user-service)...")
    app3 = App(name="user-service")
    db.add(app3)
    db.commit()
    db.refresh(app3)

    env3_dev = Environment(name="development", app_id=app3.id)
    env3_staging = Environment(name="staging", app_id=app3.id)
    env3_prod = Environment(name="production", app_id=app3.id)
    db.add_all([env3_dev, env3_staging, env3_prod])
    db.commit()
    db.refresh(env3_dev)
    db.refresh(env3_staging)
    db.refresh(env3_prod)

    # Templates for user-service
    base_json_user_dev = {
      "family": "user-service-dev",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "user-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/user:dev-latest",
          "cpu": 512,
          "memory": 1024,
          "essential": True,
          "portMappings": [{"containerPort": 4000, "hostPort": 4000}],
          "environment": [
            {"name": "PORT", "value": "4000"},
            {"name": "NODE_ENV", "value": "development"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/user-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template3_dev = TaskDefinitionTemplate(
        env_id=env3_dev.id,
        target_container="user-api",
        base_json=json.dumps(base_json_user_dev)
    )
    db.add(template3_dev)

    base_json_user_staging = {
      "family": "user-service-staging",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "user-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/user:staging-latest",
          "cpu": 1024,
          "memory": 2048,
          "essential": True,
          "portMappings": [{"containerPort": 4000, "hostPort": 4000}],
          "environment": [
            {"name": "PORT", "value": "4000"},
            {"name": "NODE_ENV", "value": "staging"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/user-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template3_staging = TaskDefinitionTemplate(
        env_id=env3_staging.id,
        target_container="user-api",
        base_json=json.dumps(base_json_user_staging)
    )
    db.add(template3_staging)

    base_json_user_prod = {
      "family": "user-service-prod",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "user-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/user:prod-latest",
          "cpu": 2048,
          "memory": 4096,
          "essential": True,
          "portMappings": [{"containerPort": 4000, "hostPort": 4000}],
          "environment": [
            {"name": "PORT", "value": "4000"},
            {"name": "NODE_ENV", "value": "production"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/user-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template3_prod = TaskDefinitionTemplate(
        env_id=env3_prod.id,
        target_container="user-api",
        base_json=json.dumps(base_json_user_prod)
    )
    db.add(template3_prod)

    # Variables y secretos de user-service
    # Development
    uv1 = Variable(env_id=env3_dev.id, key="DB_HOST", value="user-db-dev.cluster-ro.us-east-1.rds.amazonaws.com")
    uv2 = Variable(env_id=env3_dev.id, key="DB_PORT", value="5432")
    uv3 = Variable(env_id=env3_dev.id, key="CACHE_TTL_SECONDS", value="300")
    uv4 = Variable(env_id=env3_dev.id, key="LOG_LEVEL", value="DEBUG")
    uv5 = Variable(env_id=env3_dev.id, key="ENABLE_MOCK_DATA", value="true")
    us1 = Secret(env_id=env3_dev.id, key="DB_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/development/DB_PASSWORD")
    us2 = Secret(env_id=env3_dev.id, key="REDIS_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/development/REDIS_PASSWORD")
    db.add_all([uv1, uv2, uv3, uv4, uv5, us1, us2])

    # Staging
    uv6 = Variable(env_id=env3_staging.id, key="DB_HOST", value="user-db-staging.cluster-ro.us-east-1.rds.amazonaws.com")
    uv7 = Variable(env_id=env3_staging.id, key="DB_PORT", value="5432")
    uv8 = Variable(env_id=env3_staging.id, key="CACHE_TTL_SECONDS", value="600")
    uv9 = Variable(env_id=env3_staging.id, key="LOG_LEVEL", value="INFO")
    uv10 = Variable(env_id=env3_staging.id, key="ENABLE_MOCK_DATA", value="false")
    us3 = Secret(env_id=env3_staging.id, key="DB_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/staging/DB_PASSWORD")
    us4 = Secret(env_id=env3_staging.id, key="REDIS_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/staging/REDIS_PASSWORD")
    us5 = Secret(env_id=env3_staging.id, key="API_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/staging/API_KEY")
    db.add_all([uv6, uv7, uv8, uv9, uv10, us3, us4, us5])

    # Production
    uv11 = Variable(env_id=env3_prod.id, key="DB_HOST", value="user-db-prod.cluster-ro.us-east-1.rds.amazonaws.com")
    uv12 = Variable(env_id=env3_prod.id, key="DB_PORT", value="5432")
    uv13 = Variable(env_id=env3_prod.id, key="CACHE_TTL_SECONDS", value="3600")
    uv14 = Variable(env_id=env3_prod.id, key="LOG_LEVEL", value="WARN")
    uv15 = Variable(env_id=env3_prod.id, key="ENABLE_MOCK_DATA", value="false")
    uv16 = Variable(env_id=env3_prod.id, key="MAX_CONNECTIONS", value="100")
    us6 = Secret(env_id=env3_prod.id, key="DB_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/production/DB_PASSWORD")
    us7 = Secret(env_id=env3_prod.id, key="REDIS_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/production/REDIS_PASSWORD")
    us8 = Secret(env_id=env3_prod.id, key="ENCRYPTION_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/production/ENCRYPTION_KEY")
    us9 = Secret(env_id=env3_prod.id, key="ADMIN_API_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/user-service/production/ADMIN_API_KEY")
    db.add_all([uv11, uv12, uv13, uv14, uv15, uv16, us6, us7, us8, us9])

    # --- ORDER SERVICE ---
    print("Creating mock data (order-service)...")
    app4 = App(name="order-service")
    db.add(app4)
    db.commit()
    db.refresh(app4)

    env4_dev = Environment(name="development", app_id=app4.id)
    env4_staging = Environment(name="staging", app_id=app4.id)
    env4_prod = Environment(name="production", app_id=app4.id)
    db.add_all([env4_dev, env4_staging, env4_prod])
    db.commit()
    db.refresh(env4_dev)
    db.refresh(env4_staging)
    db.refresh(env4_prod)

    # Templates for order-service
    base_json_order_dev = {
      "family": "order-service-dev",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "order-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/order:dev-latest",
          "cpu": 512,
          "memory": 1024,
          "essential": True,
          "portMappings": [{"containerPort": 5000, "hostPort": 5000}],
          "environment": [
            {"name": "PORT", "value": "5000"},
            {"name": "NODE_ENV", "value": "development"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/order-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        },
        {
          "name": "order-worker",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/order-worker:dev-latest",
          "cpu": 256,
          "memory": 512,
          "essential": False,
          "environment": [
            {"name": "NODE_ENV", "value": "development"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/order-service-worker",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template4_dev = TaskDefinitionTemplate(
        env_id=env4_dev.id,
        target_container="order-api",
        base_json=json.dumps(base_json_order_dev)
    )
    db.add(template4_dev)

    # Variables y secretos de order-service (development)
    ov1 = Variable(env_id=env4_dev.id, key="DB_HOST", value="order-db-dev.cluster-ro.us-east-1.rds.amazonaws.com")
    ov2 = Variable(env_id=env4_dev.id, key="DB_PORT", value="5432")
    ov3 = Variable(env_id=env4_dev.id, key="MESSAGE_QUEUE_URL", value="https://sqs.us-east-1.amazonaws.com/123456789012/order-queue-dev")
    ov4 = Variable(env_id=env4_dev.id, key="LOG_LEVEL", value="DEBUG")
    ov5 = Variable(env_id=env4_dev.id, key="ENABLE_ORDER_VALIDATION", value="true")
    os1 = Secret(env_id=env4_dev.id, key="DB_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/order-service/development/DB_PASSWORD")
    os2 = Secret(env_id=env4_dev.id, key="QUEUE_ACCESS_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/order-service/development/QUEUE_ACCESS_KEY")
    db.add_all([ov1, ov2, ov3, ov4, ov5, os1, os2])

    # --- INVENTORY SERVICE ---
    print("Creating mock data (inventory-service)...")
    app5 = App(name="inventory-service")
    db.add(app5)
    db.commit()
    db.refresh(app5)

    env5_dev = Environment(name="development", app_id=app5.id)
    db.add(env5_dev)
    db.commit()
    db.refresh(env5_dev)

    # Template for inventory-service
    base_json_inventory_dev = {
      "family": "inventory-service-dev",
      "networkMode": "awsvpc",
      "containerDefinitions": [
        {
          "name": "inventory-api",
          "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/inventory:dev-latest",
          "cpu": 512,
          "memory": 1024,
          "essential": True,
          "portMappings": [{"containerPort": 6000, "hostPort": 6000}],
          "environment": [
            {"name": "PORT", "value": "6000"},
            {"name": "NODE_ENV", "value": "development"}
          ],
          "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "/ecs/inventory-service",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "ecs"
            }
          }
        }
      ]
    }
    
    template5_dev = TaskDefinitionTemplate(
        env_id=env5_dev.id,
        target_container="inventory-api",
        base_json=json.dumps(base_json_inventory_dev)
    )
    db.add(template5_dev)

    # Variables y secretos de inventory-service (development)
    iv1 = Variable(env_id=env5_dev.id, key="DB_HOST", value="inventory-db-dev.cluster-ro.us-east-1.rds.amazonaws.com")
    iv2 = Variable(env_id=env5_dev.id, key="DB_PORT", value="5432")
    iv3 = Variable(env_id=env5_dev.id, key="WAREHOUSE_API_URL", value="https://warehouse.internal.dev/api")
    iv4 = Variable(env_id=env5_dev.id, key="LOG_LEVEL", value="DEBUG")
    iv5 = Variable(env_id=env5_dev.id, key="INVENTORY_CHECK_INTERVAL", value="300")
    is1 = Secret(env_id=env5_dev.id, key="DB_PASSWORD", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/inventory-service/development/DB_PASSWORD")
    is2 = Secret(env_id=env5_dev.id, key="WAREHOUSE_API_KEY", ssm_path="arn:aws:ssm:us-east-1:123456789012:parameter/inventory-service/development/WAREHOUSE_API_KEY")
    db.add_all([iv1, iv2, iv3, iv4, iv5, is1, is2])

    db.commit()
    db.close()
    print("Extensive mock data created successfully!")

if __name__ == "__main__":
    seed_admin()
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        force = "--force" in sys.argv
        seed_mock_data(force=force)
