import os
import json
import uuid

class BlockManager:
    def __init__(self, blocks_dir):
        self.blocks_dir = blocks_dir
        os.makedirs(blocks_dir, exist_ok=True)
    
    def create_blocks(self, content):
        """Divide el contenido en bloques de 20 caracteres y los guarda"""
        if content is None:
            return None
        
        blocks = []
        block_size = 20
        
        # Si el contenido está vacío, crear un bloque vacío
        if not content:
            block_id = str(uuid.uuid4())
            block_path = os.path.join(self.blocks_dir, f"{block_id}.json")
            
            block_data = {
                'data': '',
                'next_block': None,
                'eof': True
            }
            
            with open(block_path, 'w', encoding='utf-8') as f:
                json.dump(block_data, f, indent=2, ensure_ascii=False)
            
            blocks.append(block_id)
        else:
            # Dividir contenido en bloques
            for i in range(0, len(content), block_size):
                block_content = content[i:i + block_size]
                block_id = str(uuid.uuid4())
                block_path = os.path.join(self.blocks_dir, f"{block_id}.json")
                
                block_data = {
                    'data': block_content,
                    'next_block': None,
                    'eof': False
                }
                
                # Guardar bloque
                with open(block_path, 'w', encoding='utf-8') as f:
                    json.dump(block_data, f, indent=2, ensure_ascii=False)
                
                blocks.append(block_id)
        
        # Enlazar bloques
        for i, block_id in enumerate(blocks):
            block_path = os.path.join(self.blocks_dir, f"{block_id}.json")
            
            with open(block_path, 'r', encoding='utf-8') as f:
                block_data = json.load(f)
            
            if i < len(blocks) - 1:
                block_data['next_block'] = blocks[i + 1]
                block_data['eof'] = False
            else:
                block_data['next_block'] = None
                block_data['eof'] = True
            
            with open(block_path, 'w', encoding='utf-8') as f:
                json.dump(block_data, f, indent=2, ensure_ascii=False)
        
        return blocks
    
    def read_blocks(self, initial_block):
        """Lee todos los bloques encadenados y retorna el contenido completo"""
        content = ""
        current_block = initial_block
        
        while current_block:
            block_path = os.path.join(self.blocks_dir, f"{current_block}.json")
            
            try:
                with open(block_path, 'r', encoding='utf-8') as f:
                    block_data = json.load(f)
                
                content += block_data['data']
                current_block = block_data['next_block']
                
                if block_data['eof']:
                    break
                    
            except (FileNotFoundError, json.JSONDecodeError):
                break
        
        return content
    
    def delete_blocks(self, initial_block):
        """Elimina todos los bloques encadenados"""
        current_block = initial_block
        
        while current_block:
            block_path = os.path.join(self.blocks_dir, f"{current_block}.json")
            
            try:
                with open(block_path, 'r', encoding='utf-8') as f:
                    block_data = json.load(f)
                
                next_block = block_data['next_block']
                
                # Eliminar archivo físico del bloque
                if os.path.exists(block_path):
                    os.remove(block_path)
                
                current_block = next_block
                
            except (FileNotFoundError, json.JSONDecodeError):
                break