import os
import json
import boto3
from dotenv import load_dotenv
import uuid
from datetime import datetime

# =========================================================================
# DATABASE.PY - Motor de Base de Datos (AWS & Docker DynamoDB)
# =========================================================================
load_dotenv()

TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "IdenteraDB")

def get_table():
    # Conexión AWS Real o DynamoDB Local
    try:
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
        
        # Si estamos ejecutando dentro de SAM local (Docker)
        if os.getenv("AWS_SAM_LOCAL") == "true":
            if not endpoint_url:
                endpoint_url = "http://dynamodb-local:8000"
            elif "localhost" in endpoint_url or "host.docker.internal" in endpoint_url:
                endpoint_url = "http://dynamodb-local:8000"
            
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "dummy"),
            endpoint_url=endpoint_url if endpoint_url else None
        )
        return dynamodb.Table(TABLE_NAME)
    except Exception as e:
        print(f"Error conectando a DynamoDB: {e}")
        return None

# =========================================================================
# FUNCIONES USUARIOS (React authService.js)
# =========================================================================

def crear_usuario_admin_por_defecto():
    """ Inyecta un admin la primera vez si no hay ninguno, para no quedarnos fuera """
    admin_correo = "admin@identera.com"
    if not obtener_usuario(admin_correo):
        crear_usuario(
             id="admin-id-123", email=admin_correo, name="Administrador Master", 
             role="ADMINISTRADOR", status="enabled", password="admin123"
        )

def crear_usuario(id: str, email: str, name: str, role: str, status: str, password: str):
    table = get_table()
    if not table: return None
    
    fecha = datetime.utcnow().isoformat()
    # Pydantic envía todo limpio, pero definimos la entidad en la base
    item = {
        "PK": f"USER#{email}",   
        "SK": f"PROFILE#{email}",
        "id": id or str(uuid.uuid4()),
        "email": email,
        "name": name,
        "role": role,
        "status": status,
        "password": password,
        "createdAt": fecha,
        "entity_type": "usuario"  
    }
    table.put_item(Item=item)
    return item

def obtener_usuario(email: str):
    table = get_table()
    if not table: return None
    res = table.get_item(Key={"PK": f"USER#{email}", "SK": f"PROFILE#{email}"})
    return res.get('Item')

def listar_usuarios():
    table = get_table()
    if not table: return []
    # En producción AWS usarías Secondary Indexes si hay millones.
    # Por ahora devolvemos todo el scan y filtramos por entidad
    res = table.scan() 
    return [i for i in res.get("Items", []) if i.get("entity_type") == "usuario"]

def eliminar_usuario(email: str):
    table = get_table()
    if table:
        table.delete_item(Key={"PK": f"USER#{email}", "SK": f"PROFILE#{email}"})

def actualizar_perfil_usuario(old_email: str, new_name: str, new_email: str, new_password: str = None):
    old_user = obtener_usuario(old_email)
    if not old_user: return None

    # Check if we are changing the email
    if old_email != new_email:
        # Prevent collisions
        if obtener_usuario(new_email):
            raise ValueError(f"Ya existe un usuario con el correo {new_email}")
        eliminar_usuario(old_email)

    table = get_table()
    if not table: return None

    # Determine final password
    password = new_password if new_password else old_user.get("password")

    item = {
        "PK": f"USER#{new_email}",
        "SK": f"PROFILE#{new_email}",
        "id": old_user.get("id"),
        "email": new_email,
        "name": new_name,
        "role": old_user.get("role"),
        "status": old_user.get("status"),
        "password": password,
        "createdAt": old_user.get("createdAt"),
        "entity_type": "usuario"
    }
    
    # Conservar campos extendidos del carnet si existen
    if "cargo" in old_user: item["cargo"] = old_user["cargo"]
    if "cedula" in old_user: item["cedula"] = old_user["cedula"]
    if "arl" in old_user: item["arl"] = old_user["arl"]
    if "eps" in old_user: item["eps"] = old_user["eps"]
    if "codigoValidador" in old_user: item["codigoValidador"] = old_user["codigoValidador"]
    if "foto" in old_user: item["foto"] = old_user["foto"]

    table.put_item(Item=item)
    return item

# =========================================================================
# FUNCIONES VALIDACIONES/CARNETS (React apiService.js)
# =========================================================================

def crear_validacion(id: str, userId: str, fecha: str, data: dict):
    table = get_table()
    if not table: return None
    
    item = {
         "PK": "VALIDACIONES_GLOBAL", # Mantenemos todas agrupadas para un Scan sencillo del listado completo
         "SK": f"VAL#{id}",
         "id": id,
         "userId": userId,
         "fecha": fecha,
         "data": data,
         "entity_type": "validacion"
    }
    table.put_item(Item=item)
    return item

def listar_validaciones():
    table = get_table()
    if not table: return []
    res = table.scan()
    return [i for i in res.get("Items", []) if i.get("entity_type") == "validacion"]

def eliminar_validacion(id: str):
    table = get_table()
    if table:
         table.delete_item(Key={"PK": "VALIDACIONES_GLOBAL", "SK": f"VAL#{id}"})

def limpiar_validaciones():
    """ Elimina todas las validaciones de la base de datos """
    table = get_table()
    if table:
        res = table.scan()
        for item in res.get("Items", []):
            if item.get("entity_type") == "validacion":
                table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

# Auto-inyectamos el administrador al arrancar el archivo (para evitar bloqueos)
try:
    crear_usuario_admin_por_defecto()
except Exception:
    pass
