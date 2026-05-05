import boto3

# Conectar al DynamoDB local
dynamodb = boto3.resource(
    'dynamodb',
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
    endpoint_url="http://localhost:8001" # El puerto expuesto por tu docker-compose
)

table = dynamodb.Table("IdenteraDB")

def migrar_urls_fotos():
    print("Iniciando migración de base de datos...")
    # Obtener todos los items
    response = table.scan()
    items = response.get('Items', [])
    
    actualizados = 0
    
    for item in items:
        modificado = False
        
        # Revisar si es un usuario
        if item.get("entity_type") == "usuario" and item.get("foto"):
            if "localhost:8000" in item["foto"]:
                item["foto"] = item["foto"].replace("localhost:8000", "127.0.0.1:3000")
                modificado = True
                
        # Revisar si es una validación/carnet
        elif item.get("entity_type") == "validacion" and item.get("data", {}).get("foto"):
            if "localhost:8000" in item["data"]["foto"]:
                item["data"]["foto"] = item["data"]["foto"].replace("localhost:8000", "127.0.0.1:3000")
                modificado = True
                
        if modificado:
            table.put_item(Item=item)
            actualizados += 1
            
    print(f"Migración completa. Se actualizaron {actualizados} registros en DynamoDB.")

if __name__ == "__main__":
    migrar_urls_fotos()
