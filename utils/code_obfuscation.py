import os
import re
import ast
import random
import string
import base64
import logging
import marshal
import binascii
import importlib
from typing import Dict, List, Set, Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class CodeObfuscator:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.key = os.urandom(32)  # AES-256 key
        self.transformations = {}
        
    def obfuscate_file(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """Làm rối một file Python

        Args:
            input_file: Đường dẫn file input
            output_file: Đường dẫn file output (mặc định là input + .obf)
        """
        try:
            # Đọc source code
            with open(input_file, 'r', encoding='utf-8') as f:
                source = f.read()
                
            # Phân tích AST
            tree = ast.parse(source)
            
            # Áp dụng các biến đổi
            tree = self._rename_variables(tree)
            tree = self._insert_junk_code(tree)
            tree = self._flatten_control_flow(tree)
            
            # Compile AST
            code = compile(tree, '<string>', 'exec')
            
            # Mã hóa bytecode
            encrypted = self._encrypt_code(marshal.dumps(code))
            
            # Tạo stub để load và decrypt
            stub = self._create_loader_stub(encrypted)
            
            # Lưu file
            if not output_file:
                output_file = input_file + '.obf'
                
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(stub)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Obfuscation error: {str(e)}")
            return False
            
    def _rename_variables(self, tree: ast.AST) -> ast.AST:
        """Đổi tên các biến thành tên ngẫu nhiên"""
        class Renamer(ast.NodeTransformer):
            def __init__(self):
                self.name_map = {}
                
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    if node.id not in self.name_map:
                        # Tạo tên mới
                        new_name = ''.join(
                            random.choices(
                                string.ascii_letters + '_',
                                k=random.randint(10, 20)
                            )
                        )
                        self.name_map[node.id] = new_name
                        
                    node.id = self.name_map[node.id]
                elif isinstance(node.ctx, ast.Load):
                    if node.id in self.name_map:
                        node.id = self.name_map[node.id]
                        
                return node
                
        renamer = Renamer()
        return renamer.visit(tree)
        
    def _insert_junk_code(self, tree: ast.AST) -> ast.AST:
        """Chèn mã rác vào để đánh lừa reverse engineering"""
        class JunkInserter(ast.NodeTransformer):
            def visit_Module(self, node):
                # Thêm imports rác
                junk_imports = [
                    'import sys',
                    'import os',
                    'import random',
                    'import time',
                    'import json'
                ]
                
                # Thêm functions rác
                junk_funcs = [
                    'def _' + ''.join(random.choices(string.ascii_lowercase, k=10)) + '():\n' +
                    '    return ' + str(random.randint(1, 1000)) + '\n'
                    for _ in range(5)
                ]
                
                # Thêm assignments rác
                junk_assigns = [
                    '_' + ''.join(random.choices(string.ascii_lowercase, k=10)) + 
                    ' = ' + str(random.randint(1, 1000)) + '\n'
                    for _ in range(5)
                ]
                
                # Parse và thêm vào tree
                junk_nodes = []
                for code in junk_imports + junk_funcs + junk_assigns:
                    junk_nodes.extend(ast.parse(code).body)
                    
                node.body = junk_nodes + node.body
                return node
                
        inserter = JunkInserter()
        return inserter.visit(tree)
        
    def _flatten_control_flow(self, tree: ast.AST) -> ast.AST:
        """Làm phẳng control flow để khó đọc hơn"""
        class ControlFlowFlattener(ast.NodeTransformer):
            def visit_If(self, node):
                # Convert if/else thành điều kiện ba ngôi
                if isinstance(node.test, ast.Compare):
                    return ast.Expr(
                        value=ast.IfExp(
                            test=node.test,
                            body=ast.Suite(body=node.body),
                            orelse=ast.Suite(body=node.orelse or [ast.Pass()])
                        )
                    )
                return node
                
            def visit_For(self, node):
                # Convert for thành while với counter
                counter = ast.Name(id='_i', ctx=ast.Store())
                test = ast.Compare(
                    left=counter,
                    ops=[ast.Lt()],
                    comparators=[ast.Call(
                        func=ast.Name(id='len', ctx=ast.Load()),
                        args=[node.iter],
                        keywords=[]
                    )]
                )
                
                return ast.While(
                    test=test,
                    body=[
                        ast.Assign(
                            targets=[node.target],
                            value=ast.Subscript(
                                value=node.iter,
                                slice=counter,
                                ctx=ast.Load()
                            )
                        )
                    ] + node.body + [
                        ast.AugAssign(
                            target=counter,
                            op=ast.Add(),
                            value=ast.Num(n=1)
                        )
                    ],
                    orelse=[]
                )
                
        flattener = ControlFlowFlattener() 
        return flattener.visit(tree)
        
    def _encrypt_code(self, code: bytes) -> bytes:
        """Mã hóa bytecode"""
        try:
            # Tạo cipher
            cipher = AES.new(self.key, AES.MODE_CBC)
            
            # Mã hóa
            encrypted = cipher.encrypt(pad(code, AES.block_size))
            
            # Trộn IV và ciphertext
            return cipher.iv + encrypted
            
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            return code
            
    def _create_loader_stub(self, encrypted_code: bytes) -> str:
        """Tạo stub code để load và chạy mã đã mã hóa"""
        # Convert key và code sang base64
        b64_key = base64.b64encode(self.key).decode()
        b64_code = base64.b64encode(encrypted_code).decode()
        
        # Template cho loader
        return f"""
import base64
import marshal
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def _load_code():
    try:
        # Decrypt key và code
        key = base64.b64decode('{b64_key}')
        encrypted = base64.b64decode('{b64_code}')
        
        # Split IV và ciphertext
        iv = encrypted[:16]
        ciphertext = encrypted[16:]
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        code = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        # Load và chạy
        exec(marshal.loads(code))
        
    except Exception as e:
        pass
        
_load_code()
"""
        
    def obfuscate_string(self, text: str) -> str:
        """Làm rối một chuỗi"""
        # Convert sang bytes
        data = text.encode()
        
        # XOR với key ngẫu nhiên
        key = os.urandom(len(data))
        xored = bytes(a ^ b for a, b in zip(data, key))
        
        # Convert sang hex
        return binascii.hexlify(xored).decode()
        
    def deobfuscate_string(self, obf_text: str) -> str:
        """Giải mã chuỗi đã làm rối"""
        try:
            # Convert từ hex
            xored = binascii.unhexlify(obf_text)
            
            # XOR với key
            key = os.urandom(len(xored))
            data = bytes(a ^ b for a, b in zip(xored, key))
            
            # Convert sang string
            return data.decode()
            
        except:
            return obf_text