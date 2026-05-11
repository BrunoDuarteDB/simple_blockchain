import os, time, hashlib, json, pyotp, qrcode, io, base64
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from extensions import db
from models import User, Block, AuditLog
from utils import derive_key

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('login.html')

# --- Registro com TOTP Cifrado (Requisito 6.vi) ---
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        
        if User.query.filter_by(username=user).first():
            flash("Usuário já existe!")
            return redirect(url_for('main.register'))
        
        salt = os.urandom(16) # 
        totp_raw = pyotp.random_base32() # Segredo em texto claro
        key = derive_key(pw, salt) # PBKDF2
        
        # Cifrando o Segredo TOTP antes de salvar
        iv_totp = os.urandom(12)# 
        aesgcm = AESGCM(key)
        totp_encrypted = aesgcm.encrypt(iv_totp, totp_raw.encode(), None)
        
        new_user = User(
            username=user,
            salt=salt.hex(),
            totp_secret=totp_encrypted.hex(), # Salvo cifrado!
            totp_iv=iv_totp.hex(),
            key_hash=hashlib.sha256(key).hexdigest()
        )
        db.session.add(new_user)
        db.session.add(AuditLog(user=user, action="Novo usuário registrado", status="SUCESSO"))
        db.session.commit()
        
        # Gera o QR Code com o segredo em texto claro (apenas para exibição única)
        totp_auth_url = pyotp.totp.TOTP(totp_raw).provisioning_uri(name=user, issuer_name="UFSC-Blockchain")
        img = qrcode.make(totp_auth_url)
        buf = io.BytesIO()
        img.save(buf)
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        return render_template('register_success.html', user=user, secret=totp_raw, qr_code=qr_base64)
    return render_template('register.html')

# --- Login com Decifragem do TOTP ---
@main_bp.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pw = request.form['password']
    token = request.form['totp']
    
    u_data = User.query.filter_by(username=user).first()
    if not u_data:
        flash("Usuário não encontrado.")
        return redirect(url_for('main.index'))
    
    key = derive_key(pw, bytes.fromhex(u_data.salt)) # 
    
    if hashlib.sha256(key).hexdigest() == u_data.key_hash:
        try:
            # Decifrando o segredo para validar o token
            aesgcm = AESGCM(key)
            totp_raw = aesgcm.decrypt(bytes.fromhex(u_data.totp_iv), bytes.fromhex(u_data.totp_secret), None).decode()
            
            if pyotp.TOTP(totp_raw).verify(token):
                session['user'] = user
                session['key'] = key.hex()
                # Log de Sucesso
                db.session.add(AuditLog(user=user, action="Login realizado", status="SUCESSO"))
                db.session.commit()
                return redirect(url_for('main.dashboard'))
        except:
            pass
    
    # Log de Falha
    db.session.add(AuditLog(user=user, action="Tentativa de login", status="FALHA"))
    db.session.commit()
    flash("Senha ou TOTP inválido!")
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('main.index'))
    
    processed_chain = []
    user_key = bytes.fromhex(session['key'])
    
    db_chain = Block.query.order_by(Block.id).all()
    chain_dicts = [{
        "owner": b.owner, "timestamp": b.timestamp, "iv": b.iv,
        "data": b.data, "prev_hash": b.prev_hash, "current_hash": b.current_hash
    } for b in db_chain]

    for i, block in enumerate(chain_dicts):
        b_copy = block.copy()
        if i > 0:
            b_copy['valid'] = (block['prev_hash'] == chain_dicts[i-1]['current_hash'])
        else:
            b_copy['valid'] = True
            
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

# --- Adição de Bloco com Verificação de Integridade (Travamento) ---
@main_bp.route('/add_block', methods=['POST'])
def add_block():
    if 'user' not in session: return redirect(url_for('main.index'))
    
    # Validação da Cadeia antes de permitir nova escrita
    db_chain = Block.query.order_by(Block.id).all()
    for i in range(1, len(db_chain)):
        if db_chain[i].prev_hash != db_chain[i-1].current_hash:
            flash("SISTEMA TRAVADO: Falha de integridade detectada na Blockchain!")
            return redirect(url_for('main.dashboard'))
    
    data = request.form['data']
    user = session['user']
    key = bytes.fromhex(session['key'])
    
    last_block = Block.query.order_by(Block.id.desc()).first()
    prev_hash = last_block.current_hash if last_block else "0"*64
    iv = os.urandom(12) 
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data.encode(), None)
    
    block = {"owner": user, "timestamp": time.strftime("%H:%M:%S"), "iv": iv.hex(), "data": ciphertext.hex(), "prev_hash": prev_hash}
    block_bytes = json.dumps(block, sort_keys=True).encode()
    block['current_hash'] = hashlib.sha256(block_bytes).hexdigest()
    
    new_block = Block(
        owner=block['owner'], 
        timestamp=block['timestamp'], 
        iv=block['iv'], 
        data=block['data'], 
        prev_hash=block['prev_hash'], 
        current_hash=block['current_hash']
    )
    db.session.add(new_block)
    db.session.commit()

    db.session.add(AuditLog(
        user=session['user'], 
        action=f"Bloco {new_block.id} minerado", 
        status="SUCESSO"
    ))
    db.session.commit()

    return redirect(url_for('main.dashboard'))

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))