# Trabalho 2 - Blockchain com Flask e PostgreSQL

Este projeto implementa uma simulação de Blockchain com autenticação 2FA (TOTP) utilizando Flask, SQLAlchemy e criptografia AES-GCM.

## Pré-requisitos

- Python 3.8+ instalado.
- PostgreSQL instalado e rodando localmente (pgAdmin recomendado).

---

## Como rodar o projeto pela primeira vez

Siga o passo a passo abaixo rigorosamente para configurar o ambiente na sua máquina.

### 1. Ambiente Virtual e Dependências
Abra o terminal na pasta do projeto e crie o ambiente virtual:
```powershell
python -m venv venv
```

Ative o ambiente virtual:
- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate`
- **Linux/Mac:** `source venv/bin/activate`

Instale as bibliotecas necessárias:
```powershell
pip install -r requirements.txt
```

### 2. Configurando as Variáveis de Ambiente (.env)
O projeto exige um arquivo `.env` para rodar, mas ele não é versionado no Git por segurança.

1. Crie um arquivo chamado **exatamente** `.env` na raiz do projeto.
2. Copie o conteúdo do arquivo `.env_exemplo.txt` para dentro do seu novo `.env`.
3. Gere uma chave secreta para o Flask rodando no terminal: `python -c "import secrets; print(secrets.token_hex(24))"` e cole no `FLASK_SECRET_KEY`.
4. Altere a `DATABASE_URL` colocando a **sua senha** do PostgreSQL no lugar de `postgres:postgres` caso seja diferente.

### 3. Criando o Banco de Dados
Abra o seu **pgAdmin** (ou psql) e crie um banco de dados vazio chamado exatamente:
**`blockchain`**
*(Não crie nenhuma tabela manualmente, o Flask Migrate fará isso!)*

### 4. Rodando as Migrações (Criando as tabelas)
Com o banco de dados criado e o `.env` configurado, aplique as migrações para gerar as tabelas `user` e `block`:

```powershell
flask db upgrade
```
*Nota: O comando `upgrade` lê a pasta `migrations` do projeto e aplica as estruturas no seu PostgreSQL local.*

### 5. Iniciando o Servidor
Agora é só rodar a aplicação:
```powershell
python app.py
```
Acesse no navegador: `http://127.0.0.1:5000`

---

## Guia de Migrações (Para os Desenvolvedores)

Se você fizer alguma alteração no arquivo `models.py` (como adicionar uma nova tabela ou uma nova coluna), o banco de dados não vai atualizar sozinho. Você precisa gerar uma nova migração!

Sempre que alterar os modelos, rode **estes dois comandos**:

**1. Gerar o molde da alteração:**
```powershell
flask db migrate -m "Mensagem descrevendo o que mudou, ex: add coluna email"
```
*(Isso vai criar um novo arquivo dentro da pasta `migrations/versions/`. Você deve "commitar" esse arquivo no Git para que o resto da equipe receba a atualização).*

**2. Aplicar a alteração no banco:**
```powershell
flask db upgrade
```