class PermissionManager:
    def can_read(self, file_info, user):
        """Verifica si el usuario tiene permiso de lectura"""
        if file_info['owner'] == user:
            return True
        
        permissions = file_info.get('permissions', {})
        return user in permissions and 'read' in permissions[user]
    
    def can_write(self, file_info, user):
        """Verifica si el usuario tiene permiso de escritura"""
        if file_info['owner'] == user:
            return True
        
        permissions = file_info.get('permissions', {})
        return user in permissions and 'write' in permissions[user]