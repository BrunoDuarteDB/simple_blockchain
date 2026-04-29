import os, time, hashlib, json, pyotp, qrcode, io, base64
from flask import Flask, render_template, request, redirect, url_for, session, flash
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)
app.secret_key = os.urandom(24) # Chave para as mensagens do Flask

# --- LÓGICA DA BLOCKCHAIN ---
class BlockchainData:
    def __init__(self):
        self.chain = []
        self.users = {} # {username: {salt, totp_secret, key_hash}}

    def derive_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

db = BlockchainData()

# --- ROTAS ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        
        if user in db.users:
            flash("Usuário já existe!")
            return redirect(url_for('register'))
        
        # 1. Parâmetros de segurança
        salt = os.urandom(16) # [cite: 66, 73]
        totp_secret = pyotp.random_base32() # [cite: 25]
        key = db.derive_key(pw, salt) # PBKDF2 
        
        # 2. Geração do QR Code (para facilitar sua vida na apresentação)
        totp_auth_url = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=user, 
            issuer_name="UFSC-Blockchain"
        )
        
        img = qrcode.make(totp_auth_url)
        buf = io.BytesIO()
        img.save(buf)
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        # 3. O que realmente salvamos (NÃO salvamos a senha nem a key pura)
        db.users[user] = {
            "salt": salt.hex(), # Único parâmetro permitido sem cifragem [cite: 73]
            "totp_secret": totp_secret,
            "key_hash": hashlib.sha256(key).hexdigest() # Para validar o login futuro
        }
        
        return render_template('register_success.html', user=user, secret=totp_secret, qr_code=qr_base64)
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pw = request.form['password']
    token = request.form['totp']
    
    if user not in db.users:
        print(f"DEBUG: Usuário {user} não encontrado!")
        flash("Usuário não encontrado.")
        return redirect(url_for('index'))
    
    u_data = db.users[user]
    key = db.derive_key(pw, bytes.fromhex(u_data['salt']))
    
    # Valida Senha e TOTP [cite: 28, 30]
    if hashlib.sha256(key).hexdigest() == u_data['key_hash']:
        totp = pyotp.TOTP(u_data['totp_secret'])
        is_valid = totp.verify(token)
        print(f"DEBUG: Senha correta! TOTP Válido? {is_valid}") # ADD ISSO
        if is_valid:
            session['user'] = user
            session['key'] = key.hex() # Chave de sessão segura [cite: 31]
            return redirect(url_for('dashboard'))
    
    flash("Senha ou TOTP inválido!")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    
    processed_chain = []
    user_key = bytes.fromhex(session['key'])
    
    for i, block in enumerate(db.chain):
        b_copy = block.copy()
        # Validação de integridade 
        if i > 0:
            b_copy['valid'] = (block['prev_hash'] == db.chain[i-1]['current_hash'])
        else:
            b_copy['valid'] = True
            
        # Decifragem apenas se for dono [cite: 42]
        if block['owner'] == session['user']:
            try:
                aesgcm = AESGCM(user_key)
                dec = aesgcm.decrypt(bytes.fromhex(block['iv']), bytes.fromhex(block['data']), None)
                b_copy['decrypted_data'] = dec.decode()
            except:
                b_copy['decrypted_data'] = "ERRO NA DECIFRAGEM"
        else:
            b_copy['decrypted_data'] = "[CONTEÚDO CRIPTOGRAFADO]"
        processed_chain.append(b_copy)
        
    return render_template('dashboard.html', chain=processed_chain)

@app.route('/add_block', methods=['POST'])
def add_block():
    if 'user' not in session: return redirect(url_for('index'))
    
    data = request.form['data']
    user = session['user']
    key = bytes.fromhex(session['key'])
    
    prev_hash = db.chain[-1]['current_hash'] if db.chain else "0"*64
    iv = os.urandom(12) # IV Único por bloco [cite: 35, 47]
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data.encode(), None)
    
    block = {
        "owner": user,
        "timestamp": time.strftime("%H:%M:%S"),
        "iv": iv.hex(),
        "data": ciphertext.hex(),
        "prev_hash": prev_hash
    }
    
    # Gerar hash do bloco atual [cite: 12]
    block_bytes = json.dumps(block, sort_keys=True).encode()
    block['current_hash'] = hashlib.sha256(block_bytes).hexdigest()
    
    db.chain.append(block)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)