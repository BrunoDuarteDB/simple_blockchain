# reset.ps1
Write-Host "--- Limpeza total do ambiente ---" -ForegroundColor Yellow

# 1. Remove a pasta local de migrações
if (Test-Path "migrations") {
    Remove-Item -Recurse -Force "migrations"
    Write-Host "[OK] Pasta migrations removida." -ForegroundColor Green
}

# 2. Limpa o banco de dados via Python (Tabelas + Versão do Alembic)
python -c "from app import create_app; from extensions import db; from sqlalchemy import text; app=create_app(); ctx=app.app_context(); ctx.push(); db.drop_all(); db.session.execute(text('DROP TABLE IF EXISTS alembic_version')); db.session.commit(); print('[OK] PostgreSQL limpo com sucesso.')"

# 3. Recria a estrutura do zero
flask db init
flask db migrate -m "Reset com AuditLog e TOTP Cifrado"
flask db upgrade

Write-Host "--- Ambiente pronto para uso ---" -ForegroundColor Cyan