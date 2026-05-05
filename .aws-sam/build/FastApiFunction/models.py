from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

# =========================================================================
# MODELS.PY - El escudo de tu base de datos (VERSIÓN INTEGRADA)
# =========================================================================
# Protege y estandariza los datos entre React (Frontend) y DynamoDB (Nube).

class UsuarioBase(BaseModel):
    id: Optional[str] = Field(None, description="ID único. Se usa el correo como referencia real.")
    email: EmailStr = Field(..., description="Correo electrónico (llave principal)")
    name: str = Field(..., description="Nombre completo")
    role: str = Field(default="USUARIO", description="ADMINISTRADOR, SEGURIDAD o USUARIO")
    status: str = Field(default="enabled", description="enabled o disabled")
    password: str = Field(..., description="Contraseña de acceso")
    createdAt: Optional[str] = Field(None, description="Fecha de creación")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Modelo para los roles y estatus
class UpdateStatusRequest(BaseModel):
    status: str

class UpdateRoleRequest(BaseModel):
    role: str

class UpdateUserProfileRequest(BaseModel):
    email: EmailStr
    name: str
    password: Optional[str] = None

class ValidacionBase(BaseModel):
    """
    Representa un Carnet o Escaneo que fue guardado desde el Frontend.
    """
    id: str = Field(..., description="ID del carnet generado por React")
    userId: str = Field(..., description="A quién le pertenece el carnet (correo/id)")
    fecha: str = Field(..., description="Fecha ISO en la que se generó/validó")
    data: Dict[str, Any] = Field(default_factory=dict, description="Metadata del carnet (foto, codigo, etc)")
