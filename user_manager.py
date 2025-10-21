import json
import os
from datetime import datetime

class UserManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        os.makedirs(data_dir, exist_ok=True)
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Inicializa el archivo de usuarios con el usuario admin por defecto"""
        if not os.path.exists(self.users_file):
            default_users = {
                "admin": {
                    "password": "admin123",
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
            self._save_users(default_users)
    
    def _load_users(self):
        """Carga los usuarios desde el archivo JSON"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"Error cargando usuarios: {e}")
            return {
                "admin": {
                    "password": "admin123",
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
    
    def _save_users(self, users):
        """Guarda los usuarios en el archivo JSON"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando usuarios: {e}")
            return False
    
    def authenticate(self, username, password):
        """Autentica un usuario"""
        try:
            users = self._load_users()
            
            if username in users and users[username]["password"] == password:
                return True, users[username]["role"]
            return False, None
        except Exception as e:
            print(f"Error en autenticación: {e}")
            return False, None
    
    def create_user(self, username, password, role="user", admin_username=None):
        """Crea un nuevo usuario (solo admin puede crear usuarios)"""
        try:
            users = self._load_users()
            
            if admin_username:
                if admin_username not in users:
                    return False, "Usuario administrador no existe"
                if users[admin_username]["role"] != "admin":
                    return False, "Solo los administradores pueden crear usuarios"
            
            if username in users:
                return False, "El usuario ya existe"
            
            if len(password) < 4:
                return False, "La contraseña debe tener al menos 4 caracteres"
            
            if role not in ["user", "admin"]:
                return False, "Rol inválido. Debe ser 'user' o 'admin'"
            
            users[username] = {
                "password": password,
                "role": role,
                "created_at": datetime.now().isoformat()
            }
            
            if self._save_users(users):
                return True, "Usuario creado exitosamente"
            else:
                return False, "Error al guardar el usuario"
                
        except Exception as e:
            return False, f"Error creando usuario: {str(e)}"
    
    def user_exists(self, username):
        """Verifica si un usuario existe"""
        try:
            users = self._load_users()
            return username in users
        except Exception:
            return False
    
    def get_all_users(self):
        """Obtiene todos los usuarios"""
        try:
            return self._load_users()
        except Exception:
            return {}
    
    def get_user_role(self, username):
        """Obtiene el rol de un usuario"""
        try:
            users = self._load_users()
            if username in users:
                return users[username]["role"]
            return None
        except Exception:
            return None
    
    def delete_user(self, username, admin_username):
        """Elimina un usuario (solo admin)"""
        try:
            users = self._load_users()
            
            if admin_username not in users or users[admin_username]["role"] != "admin":
                return False, "Solo los administradores pueden eliminar usuarios"
            if username == admin_username:
                return False, "No puede eliminar su propio usuario"
            
            if username not in users:
                return False, "El usuario no existe"
            
            del users[username]
            
            if self._save_users(users):
                return True, "Usuario eliminado exitosamente"
            else:
                return False, "Error al guardar los cambios"
                
        except Exception as e:
            return False, f"Error eliminando usuario: {str(e)}"
    
    def change_password(self, username, old_password, new_password):
        """Cambia la contraseña de un usuario"""
        try:
            users = self._load_users()
            
            if username not in users:
                return False, "Usuario no existe"
            
            if users[username]["password"] != old_password:
                return False, "Contraseña actual incorrecta"
            
            if len(new_password) < 4:
                return False, "La nueva contraseña debe tener al menos 4 caracteres"
            
            users[username]["password"] = new_password
            
            if self._save_users(users):
                return True, "Contraseña cambiada exitosamente"
            else:
                return False, "Error al guardar la nueva contraseña"
                
        except Exception as e:
            return False, f"Error cambiando contraseña: {str(e)}"