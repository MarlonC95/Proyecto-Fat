import os
import json
from datetime import datetime
from block_manager import BlockManager
from permission_manager import PermissionManager
import zipfile
import shutil

class FATFileSystem:
    def __init__(self):
        self.data_dir = "data"
        self.fat_table_path = os.path.join(self.data_dir, "fat_table.json")
        self.blocks_dir = os.path.join(self.data_dir, "blocks")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.large_files_dir = os.path.join(self.data_dir, "large_files")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.block_manager = BlockManager(self.blocks_dir)
        self.permission_manager = PermissionManager()
        
    def initialize_system(self):
        """Inicializa el sistema creando directorios necesarios"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.blocks_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.large_files_dir, exist_ok=True)
        
        if not os.path.exists(self.fat_table_path):
            self._save_fat_table({})
    
    def _load_fat_table(self):
        """Carga la tabla FAT desde el archivo JSON"""
        try:
            with open(self.fat_table_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_fat_table(self, fat_table):
        """Guarda la tabla FAT en el archivo JSON"""
        with open(self.fat_table_path, 'w', encoding='utf-8') as f:
            json.dump(fat_table, f, indent=2, ensure_ascii=False)
    
    def create_file(self, filename, content, owner, is_binary=False):
        """Crea un nuevo archivo en el sistema"""
        fat_table = self._load_fat_table()
        
        if filename in fat_table:
            return False  # Archivo ya existe
        
        # Para archivos binarios grandes, usar almacenamiento directo
        if is_binary and len(content) > 1000000:  # Más de 1MB
            return self._create_large_binary_file(filename, content, owner, fat_table)
        
        # Crear bloques de datos
        block_chain = self.block_manager.create_blocks(content)
        if not block_chain:
            return False
        
        # Crear entrada en la tabla FAT
        current_time = datetime.now().isoformat()
        fat_table[filename] = {
            'filename': filename,
            'initial_block': block_chain[0],
            'in_recycle_bin': False,
            'total_chars': len(content),
            'creation_date': current_time,
            'modification_date': current_time,
            'deletion_date': None,
            'owner': owner,
            'is_binary': is_binary,
            'is_large_file': False,
            'permissions': {owner: ['read', 'write']}
        }
        
        self._save_fat_table(fat_table)
        return True
    
    def _create_large_binary_file(self, filename, content, owner, fat_table):
        """Crea archivos binarios grandes con almacenamiento directo"""
        try:
            # Guardar archivo directamente
            file_path = os.path.join(self.large_files_dir, f"{filename}.bin")
            with open(file_path, 'wb') as f:
                if isinstance(content, str):
                    # Si es base64 string, decodificar primero
                    import base64
                    content = base64.b64decode(content)
                f.write(content)
            
            current_time = datetime.now().isoformat()
            fat_table[filename] = {
                'filename': filename,
                'file_path': file_path,
                'in_recycle_bin': False,
                'total_chars': len(content),
                'creation_date': current_time,
                'modification_date': current_time,
                'deletion_date': None,
                'owner': owner,
                'is_binary': True,
                'is_large_file': True,
                'permissions': {owner: ['read', 'write']}
            }
            
            self._save_fat_table(fat_table)
            return True
        except Exception as e:
            print(f"Error creando archivo grande: {e}")
            return False
    
    def open_file(self, filename, user):
        """Abre un archivo y retorna su contenido"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return None, "Archivo no encontrado"
        
        file_info = fat_table[filename]
        
        # Verificar permisos
        if not self.permission_manager.can_read(file_info, user):
            return None, "Permiso denegado"
        
        # Para archivos grandes, leer directamente del archivo
        if file_info.get('is_large_file', False):
            try:
                file_path = file_info['file_path']
                with open(file_path, 'rb') as f:
                    content = f.read()
                # Convertir a base64 para consistencia
                import base64
                content = base64.b64encode(content).decode('utf-8')
                return file_info, content
            except Exception as e:
                return None, f"Error leyendo archivo grande: {str(e)}"
        
        # Leer contenido de los bloques
        content = self.block_manager.read_blocks(file_info['initial_block'])
        return file_info, content
    
    def list_files(self):
        """Lista todos los archivos que no están en la papelera"""
        fat_table = self._load_fat_table()
        return [file_info for file_info in fat_table.values() 
                if not file_info['in_recycle_bin']]
    
    def list_recycle_bin(self):
        """Lista todos los archivos en la papelera"""
        fat_table = self._load_fat_table()
        return [file_info for file_info in fat_table.values() 
                if file_info['in_recycle_bin']]
    
    def modify_file(self, filename, new_content, user):
        """Modifica el contenido de un archivo"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Verificar permisos de escritura
        if not self.permission_manager.can_write(file_info, user):
            return False
        
        # Para archivos grandes
        if file_info.get('is_large_file', False):
            try:
                file_path = file_info['file_path']
                with open(file_path, 'wb') as f:
                    if isinstance(new_content, str):
                        import base64
                        new_content = base64.b64decode(new_content)
                    f.write(new_content)
                
                file_info['total_chars'] = len(new_content)
                file_info['modification_date'] = datetime.now().isoformat()
                self._save_fat_table(fat_table)
                return True
            except Exception as e:
                print(f"Error modificando archivo grande: {e}")
                return False
        
        # Eliminar bloques antiguos
        self.block_manager.delete_blocks(file_info['initial_block'])
        
        # Crear nuevos bloques
        new_block_chain = self.block_manager.create_blocks(new_content)
        if not new_block_chain:
            return False
        
        # Actualizar tabla FAT
        file_info['initial_block'] = new_block_chain[0]
        file_info['total_chars'] = len(new_content)
        file_info['modification_date'] = datetime.now().isoformat()
        
        self._save_fat_table(fat_table)
        return True
    
    def delete_file(self, filename, user):
        """Mueve un archivo a la papelera"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Solo el propietario puede eliminar
        if file_info['owner'] != user:
            return False
        
        file_info['in_recycle_bin'] = True
        file_info['deletion_date'] = datetime.now().isoformat()
        
        self._save_fat_table(fat_table)
        return True
    
    def delete_file_permanently(self, filename, user):
        """Elimina un archivo permanentemente del sistema"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Solo el propietario puede eliminar permanentemente
        if file_info['owner'] != user:
            return False
        
        # Eliminar bloques de datos
        if not file_info.get('is_large_file', False):
            self.block_manager.delete_blocks(file_info['initial_block'])
        else:
            # Eliminar archivo grande
            try:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
            except Exception:
                pass
        
        # Eliminar de la tabla FAT
        del fat_table[filename]
        self._save_fat_table(fat_table)
        return True
    
    def recover_file(self, filename, user):
        """Recupera un archivo de la papelera"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Solo el propietario puede recuperar
        if file_info['owner'] != user:
            return False
        
        file_info['in_recycle_bin'] = False
        file_info['deletion_date'] = None
        
        self._save_fat_table(fat_table)
        return True
    
    def get_file_info(self, filename):
        """Obtiene información de un archivo"""
        fat_table = self._load_fat_table()
        return fat_table.get(filename)
    
    def grant_permission(self, filename, owner, user, permission):
        """Concede un permiso a un usuario"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Solo el propietario puede conceder permisos
        if file_info['owner'] != owner:
            return False
        
        if permission not in ['read', 'write']:
            return False
        
        if user not in file_info['permissions']:
            file_info['permissions'][user] = []
        
        if permission not in file_info['permissions'][user]:
            file_info['permissions'][user].append(permission)
        
        self._save_fat_table(fat_table)
        return True
    
    def revoke_permission(self, filename, owner, user, permission):
        """Revoca un permiso de un usuario"""
        fat_table = self._load_fat_table()
        
        if filename not in fat_table:
            return False
        
        file_info = fat_table[filename]
        
        # Solo el propietario puede revocar permisos
        if file_info['owner'] != owner:
            return False
        
        if user in file_info['permissions'] and permission in file_info['permissions'][user]:
            file_info['permissions'][user].remove(permission)
            # Si no quedan permisos, eliminar usuario
            if not file_info['permissions'][user]:
                del file_info['permissions'][user]
        
        self._save_fat_table(fat_table)
        return True
    
    def create_backup(self, backup_name=None):
        """Crea un backup completo del sistema"""
        try:
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            # Asegurarse de que el directorio de backups existe
            os.makedirs(self.backup_dir, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup de la tabla FAT
                if os.path.exists(self.fat_table_path):
                    zipf.write(self.fat_table_path, 'fat_table.json')
                    print(f"Backup de tabla FAT: {self.fat_table_path}")
                
                # Backup de usuarios
                if os.path.exists(self.users_file):
                    zipf.write(self.users_file, 'users.json')
                    print(f"Backup de usuarios: {self.users_file}")
                
                # Backup de los bloques
                if os.path.exists(self.blocks_dir):
                    for root, dirs, files in os.walk(self.blocks_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.data_dir)
                            zipf.write(file_path, arcname)
                            print(f"Backup de bloque: {file_path}")
                
                # Backup de archivos grandes
                if os.path.exists(self.large_files_dir):
                    for root, dirs, files in os.walk(self.large_files_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.data_dir)
                            zipf.write(file_path, arcname)
                            print(f"Backup de archivo grande: {file_path}")
            
            # Verificar que el backup se creó correctamente
            if os.path.exists(backup_path):
                file_size = os.path.getsize(backup_path)
                return True, f"Backup creado exitosamente: {backup_name}.zip ({file_size / 1024 / 1024:.2f} MB)"
            else:
                return False, "Error: No se pudo crear el archivo de backup"
                
        except Exception as e:
            return False, f"Error creando backup: {str(e)}"
    
    def restore_backup(self, backup_path):
        """Restaura el sistema desde un backup"""
        try:
            # Verificar que el archivo de backup existe
            if not os.path.exists(backup_path):
                return False, "El archivo de backup no existe"
            
            # Crear backup actual antes de restaurar
            self.create_backup("pre_restore_backup")
            
            # Limpiar datos actuales
            self._clean_system_data()
            
            # Extraer backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.data_dir)
            
            # Verificar que los archivos esenciales existen
            essential_files = [self.fat_table_path, self.users_file]
            for file_path in essential_files:
                if not os.path.exists(file_path):
                    return False, f"Archivo esencial faltante en backup: {os.path.basename(file_path)}"
            
            return True, "Backup restaurado exitosamente"
            
        except Exception as e:
            return False, f"Error restaurando backup: {str(e)}"
    
    def _clean_system_data(self):
        """Limpia los datos del sistema actual"""
        try:
            # Eliminar bloques
            if os.path.exists(self.blocks_dir):
                shutil.rmtree(self.blocks_dir)
                os.makedirs(self.blocks_dir)
            
            # Eliminar archivos grandes
            if os.path.exists(self.large_files_dir):
                shutil.rmtree(self.large_files_dir)
                os.makedirs(self.large_files_dir)
            
            # Reiniciar tabla FAT
            self._save_fat_table({})
            
        except Exception as e:
            print(f"Error limpiando datos del sistema: {e}")
    
    def list_backups(self):
        """Lista todos los backups disponibles"""
        backups = []
        try:
            if os.path.exists(self.backup_dir):
                for file in os.listdir(self.backup_dir):
                    if file.endswith('.zip'):
                        file_path = os.path.join(self.backup_dir, file)
                        stats = os.stat(file_path)
                        backups.append({
                            'name': file,
                            'path': file_path,
                            'size': stats.st_size,
                            'created': datetime.fromtimestamp(stats.st_ctime).isoformat()
                        })
                # Ordenar por fecha de creación (más reciente primero)
                backups.sort(key=lambda x: x['created'], reverse=True)
        except Exception as e:
            print(f"Error listando backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_name):
        """Elimina un backup específico"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True, f"Backup {backup_name} eliminado exitosamente"
            else:
                return False, "El backup no existe"
        except Exception as e:
            return False, f"Error eliminando backup: {str(e)}"