
# Trabalho 2 - Blockchain com Flask e PostgreSQL

Este projeto implementa uma simulação de Blockchain com autenticação 2FA (TOTP) utilizando Flask, SQLAlchemy e criptografia AES-GCM.

## Especificações Técnicas de Segurança

* **Criptografia de Dados**: Utilização de **AES-GCM** para garantir a confidencialidade e a integridade dos blocos armazenados no banco de dados.
* **Derivação de Chave**: As chaves de criptografia são geradas via **PBKDF2-HMAC-SHA256** com 100.000 iterações e Salt aleatório de 16 bytes.
* **Proteção de Parâmetros**: Em conformidade com o requisito 6.vi da disciplina, o segredo TOTP é armazenado cifrado no banco de dados. Apenas o Salt permanece em texto claro.
* **Integridade e Travamento**: O sistema verifica a validade da cadeia através do `hash_prev` antes de cada nova escrita. Caso uma alteração inválida seja detectada, o sistema bloqueia novas adições.
* **Auditoria**: Registro automático de tentativas de login e operações de mineração na tabela **AuditLog** para fins de rastreabilidade.

## Pré-requisitos

* Python 3.8+ instalado.
* PostgreSQL instalado e rodando localmente (pgAdmin recomendado).

---

## Como rodar o projeto pela primeira vez

Siga o passo a passo abaixo rigorosamente para configurar o ambiente na sua máquina.

### 1. Ambiente Virtual e Dependências
Abra o terminal na pasta do projeto e crie o ambiente virtual:
```bash
python -m venv venv

```

Ative o ambiente virtual:

* **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
* **Windows (CMD)**: `venv\Scripts\activate`
* **Linux/Mac**: `source venv/bin/activate`

Instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt

```

### 2. Configurando as Variáveis de Ambiente (.env)

O projeto exige um arquivo `.env` para rodar, que não é versionado no Git por segurança.

1. Crie um arquivo chamado exatamente `.env` na raiz do projeto.
2. Copie o conteúdo do arquivo `.env_exemplo.txt` para dentro do seu novo `.env`.
3. Gere uma chave secreta para o Flask rodando no terminal: `python -c "import secrets; print(secrets.token_hex(24))"` e cole no campo `FLASK_SECRET_KEY`.
4. Altere a `DATABASE_URL` inserindo a sua senha do PostgreSQL no lugar de `postgres:postgres` caso seja diferente da padrão.

### 3. Criando o Banco de Dados

Abra o seu pgAdmin (ou psql) e crie um banco de dados vazio chamado exatamente: **blockchain**.

### 4. Inicialização e Limpeza do Banco

Para configurar a estrutura inicial ou resetar o ambiente garantindo a limpeza de migrações antigas e tabelas de versão, utilize o script de automação multiplataforma:

```bash
python reset.py

```

*Este script remove a pasta de migrações local, limpa as tabelas existentes no PostgreSQL (incluindo a tabela interna alembic_version) e recria as tabelas User, Block e AuditLog.*

### 5. Iniciando o Servidor

Com o ambiente configurado, execute a aplicação:

```bash
python app.py

```

Acesse no navegador: `http://127.0.0.1:5000`.

---

## Guia de Migrações (Para os Desenvolvedores)

Se houver alguma alteração no arquivo `models.py`, o banco de dados deve ser atualizado. Para alterações simples no esquema, utilize os comandos padrão do Flask-Migrate. Caso deseje realizar uma limpeza completa e reiniciar o esquema do banco, utilize o script `reset.py`.

**1. Gerar o molde da alteração**:

```bash
flask db migrate -m "Descricao da alteracao"

```

**2. Aplicar a alteração no banco**:

```bash
flask db upgrade

```
