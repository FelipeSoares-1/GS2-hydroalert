"""
Sistema de Segurança para HydroAlert
Global Solution 2025.1 - FIAP
Grupo 35 - Componente de Cibersegurança
"""

import hashlib
import secrets
import jwt
import logging
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import json
import os
from functools import wraps
import streamlit as st

class HydroAlertSecurity:
    """
    Classe principal de segurança do sistema HydroAlert
    Implementa autenticação, criptografia e logs de segurança
    """
    
    def __init__(self):
        self.secret_key = self._generate_secret_key()
        self.fernet = Fernet(Fernet.generate_key())
        self.security_log_file = "data/security_logs.json"
        self._setup_logging()
    
    def _generate_secret_key(self):
        """Gera chave secreta para JWT"""
        return secrets.token_urlsafe(32)
    
    def _setup_logging(self):
        """Configura logging de segurança"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/security.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('HydroAlertSecurity')
    
    def hash_password(self, password: str) -> str:
        """
        Cria hash seguro da senha usando SHA-256 + salt
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica se a senha corresponde ao hash
        """
        try:
            salt, stored_hash = hashed.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except ValueError:
            return False
    
    def generate_token(self, user_id: str, role: str = "user") -> str:
        """
        Gera token JWT para autenticação
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        self.log_security_event("token_generated", {
            "user_id": user_id,
            "role": role,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """
        Verifica e decodifica token JWT
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            self.log_security_event("token_expired", {
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
        except jwt.InvalidTokenError:
            self.log_security_event("token_invalid", {
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
    
    def encrypt_sensor_data(self, data: str) -> str:
        """
        Criptografa dados dos sensores
        """
        encrypted_data = self.fernet.encrypt(data.encode())
        return encrypted_data.hex()
    
    def decrypt_sensor_data(self, encrypted_data: str) -> str:
        """
        Descriptografa dados dos sensores
        """
        try:
            encrypted_bytes = bytes.fromhex(encrypted_data)
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Erro na descriptografia: {e}")
            return None
    
    def log_security_event(self, event_type: str, details: dict):
        """
        Registra eventos de segurança
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        # Log no arquivo
        self.logger.info(f"Security Event: {event_type} - {details}")
        
        # Salvar em arquivo JSON
        try:
            if os.path.exists(self.security_log_file):
                with open(self.security_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            
            # Manter apenas os últimos 1000 logs
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.security_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de segurança: {e}")
    
    def validate_sensor_input(self, data: dict) -> bool:
        """
        Valida entrada de dados dos sensores para prevenir ataques
        """
        required_fields = ['rainfall', 'water_level', 'soil_moisture', 'timestamp']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in data:
                self.log_security_event("invalid_sensor_data", {
                    "reason": f"Missing field: {field}",
                    "data": str(data)
                })
                return False
        
        # Validar tipos e ranges
        try:
            rainfall = float(data['rainfall'])
            water_level = float(data['water_level'])
            soil_moisture = float(data['soil_moisture'])
            
            # Validar ranges realistas
            if not (0 <= rainfall <= 200):  # mm/h
                raise ValueError("Rainfall out of range")
            if not (0 <= water_level <= 1000):  # cm
                raise ValueError("Water level out of range")
            if not (0 <= soil_moisture <= 100):  # %
                raise ValueError("Soil moisture out of range")
                
        except (ValueError, TypeError) as e:
            self.log_security_event("invalid_sensor_data", {
                "reason": str(e),
                "data": str(data)
            })
            return False
        
        return True

# Usuários pré-definidos do sistema (em produção seria banco de dados)
USERS_DB = {
    "admin": {
        "password_hash": "",  # Será definido na inicialização
        "role": "admin",
        "name": "Administrador Sistema"
    },
    "defesa_civil": {
        "password_hash": "",
        "role": "operator",
        "name": "Defesa Civil"
    },
    "viewer": {
        "password_hash": "",
        "role": "viewer",
        "name": "Visualizador"
    }
}

def init_security_system():
    """
    Inicializa sistema de segurança
    """
    security = HydroAlertSecurity()
    
    # Definir senhas padrão (em produção seria configurado de forma segura)
    default_passwords = {
        "admin": "HydroAlert2025!",
        "defesa_civil": "DefesaCivil123",
        "viewer": "Viewer2025"
    }
    
    # Criar hashes das senhas
    for username, password in default_passwords.items():
        if username in USERS_DB:
            USERS_DB[username]["password_hash"] = security.hash_password(password)
    
    security.log_security_event("system_initialized", {
        "users_created": len(USERS_DB),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return security

def authenticate_user(username: str, password: str) -> dict:
    """
    Autentica usuário no sistema
    """
    security = HydroAlertSecurity()
    
    if username not in USERS_DB:
        security.log_security_event("login_failed", {
            "username": username,
            "reason": "User not found"
        })
        return None
    
    user = USERS_DB[username]
    if security.verify_password(password, user["password_hash"]):
        token = security.generate_token(username, user["role"])
        
        security.log_security_event("login_successful", {
            "username": username,
            "role": user["role"]
        })
        
        return {
            "username": username,
            "role": user["role"],
            "name": user["name"],
            "token": token
        }
    else:
        security.log_security_event("login_failed", {
            "username": username,
            "reason": "Invalid password"
        })
        return None

def require_auth(required_role: str = "viewer"):
    """
    Decorator para requerer autenticação em funções
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'authenticated_user' not in st.session_state:
                st.error("🔐 Acesso negado. Faça login primeiro.")
                return None
            
            user_role = st.session_state.authenticated_user['role']
            role_hierarchy = {"viewer": 0, "operator": 1, "admin": 2}
            
            if role_hierarchy.get(user_role, -1) < role_hierarchy.get(required_role, 999):
                st.error(f"🔐 Acesso negado. Permissão '{required_role}' necessária.")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def create_login_page():
    """
    Cria página de login do sistema
    """
    st.title("🔐 HydroAlert - Login Seguro")
    st.markdown("### Sistema de Previsão de Inundações Urbanas")
    
    if 'authenticated_user' in st.session_state:
        st.success(f"✅ Logado como: {st.session_state.authenticated_user['name']}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚪 Logout"):
                del st.session_state.authenticated_user
                st.rerun()
        
        return True
    
    with st.form("login_form"):
        st.subheader("Credenciais de Acesso")
        username = st.text_input("👤 Usuário")
        password = st.text_input("🔑 Senha", type="password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("🔓 Entrar")
        
        if submit:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated_user = user
                    st.success(f"✅ Login realizado com sucesso! Bem-vindo, {user['name']}")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas")
            else:
                st.warning("⚠️ Preencha todos os campos")
    
    # Informações de usuários de teste
    with st.expander("ℹ️ Usuários de Demonstração"):
        st.markdown("""
        **Usuários disponíveis para teste:**
        - **admin** / HydroAlert2025! (Administrador)
        - **defesa_civil** / DefesaCivil123 (Operador)
        - **viewer** / Viewer2025 (Visualizador)
        """)
    
    return False

# Exemplo de uso do sistema de segurança
if __name__ == "__main__":
    # Inicializar sistema
    security = init_security_system()
    
    print("🔐 Sistema de Segurança HydroAlert Inicializado")
    print("✅ Criptografia configurada")
    print("✅ Autenticação configurada") 
    print("✅ Logs de segurança configurados")
    print("✅ Validação de dados configurada")
