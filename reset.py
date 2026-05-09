import os
import shutil
import subprocess
import sys

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar: {command}\n{e}")

print("--- Limpeza total do ambiente ---")

# 1. Remove a pasta de migrações
if os.path.exists("migrations"):
    shutil.rmtree("migrations")
    print("[OK] Pasta migrations removida.")

# 2. Limpa o banco via Python
clean_db_cmd = (
    f"{sys.executable} -c \"from app import create_app; from extensions import db; "
    "from sqlalchemy import text; app=create_app(); ctx=app.app_context(); ctx.push(); "
    "db.drop_all(); db.session.execute(text('DROP TABLE IF EXISTS alembic_version')); "
    "db.session.commit(); print('[OK] PostgreSQL limpo com sucesso.')\""
)
run_command(clean_db_cmd)

# 3. Recria a estrutura
print("Recriando estrutura do zero...")
run_command("flask db init")
run_command("flask db migrate -m \"Reset com AuditLog e TOTP Cifrado\"")
run_command("flask db upgrade")

print("--- Ambiente pronto para uso ---")