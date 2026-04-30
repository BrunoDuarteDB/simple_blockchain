import os, time, hashlib, json, pyotp, qrcode, io, base64
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from extensions import db
from models import User, Block
from utils import derive_key

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        
        if User.query.filter_by(username=user).first():
            flash("Usuário já existe!")
            return redirect(url_for('main.register'))
        
        # 1. Parâmetros de segurança
        salt = os.urandom(16) # [cite: 66, 73]
        totp_secret = pyotp.random_base32() # [cite: 25]
        key = derive_key(pw, salt) # PBKDF2 
        
        # 2. Geração do QR Code
        totp_auth_url = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=user, 
            issuer_name="UFSC-Blockchain"
        )
        
        img = qrcode.make(totp_auth_url)
        buf = io.BytesIO()
        img.save(buf)
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        # 3. O que realmente salvamos
        new_user = User(
            username=user,
            salt=salt.hex(), 
            totp_secret=totp_secret,
            key_hash=hashlib.sha256(key).hexdigest() 
        )
        db.session.add(new_user)
        db.session.commit()
        
        return render_template('register_success.html', user=user, secret=totp_secret, qr_code=qr_base64)
    
    return render_template('register.html')

@main_bp.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pw = request.form['password']
    token = request.form['totp']
    
    u_data = User.query.filter_by(username=user).first()
    if not u_data:
        print(f"DEBUG: Usuário {user} não encontrado!")
        flash("Usuário não encontrado.")
        return redirect(url_for('main.index'))
    
    key = derive_key(pw, bytes.fromhex(u_data.salt))
    
    # Valida Senha e TOTP
    if hashlib.sha256(key).hexdigest() == u_data.key_hash:
        totp = pyotp.TOTP(u_data.totp_secret)
        is_valid = totp.verify(token)
        print(f"DEBUG: Senha correta! TOTP Válido? {is_valid}")
        if is_valid:
            session['user'] = user
            session['key'] = key.hex() 
            return redirect(url_for('main.dashboard'))
    
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

@main_bp.route('/add_block', methods=['POST'])
def add_block():
    if 'user' not in session: return redirect(url_for('main.index'))
    
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
    
    new_block = Block(owner=block['owner'], timestamp=block['timestamp'], iv=block['iv'], data=block['data'], prev_hash=block['prev_hash'], current_hash=block['current_hash'])
    db.session.add(new_block)
    db.session.commit()

    return redirect(url_for('main.dashboard'))

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))