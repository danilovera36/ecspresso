import json
import os

def merge_td(base_json_str: str, target_container: str, variables: list, secrets: list) -> dict:
    """
    SMART MERGE (Aditivo):
    En lugar de sobreescribir las listas, convierte las existentes en diccionarios,
    actualiza con lo que trae ecspresso, y las devuelve como lista.
    Así no se pierden variables fijas que el DevOps puso en el JSON base.
    """
    td = json.loads(base_json_str)
    
    # Creamos diccionarios de lo que maneja ecspresso: {"KEY": {"name": "KEY", "value": "VAL"}}
    ecspresso_vars = {v.key: {"name": v.key, "value": v.value} for v in variables}
    
    region = os.getenv("AWS_REGION", "us-east-1")
    account = os.getenv("AWS_ACCOUNT_ID", "123456789012")
    ecspresso_secrets = {
        s.key: {"name": s.key, "valueFrom": f"arn:aws:ssm:{region}:{account}:parameter{s.ssm_path}"} 
        for s in secrets
    }
    
    for container in td.get("containerDefinitions", []):
        if container["name"] == target_container:
            # 1. Obtener lo que ya existe en el JSON base y convertirlo a dict
            existing_vars = {env["name"]: env for env in container.get("environment", [])}
            existing_secrets = {sec["name"]: sec for sec in container.get("secrets", [])}
            
            # 2. El Smart Merge: ecspresso pisa las que tienen el mismo nombre, pero NO borra las otras
            existing_vars.update(ecspresso_vars)
            existing_secrets.update(ecspresso_secrets)
            
            # 3. Volver a convertir a lista para el JSON final de ECS
            container["environment"] = list(existing_vars.values())
            container["secrets"] = list(existing_secrets.values())
            break # Solo modificamos el contenedor objetivo
            
    return td
