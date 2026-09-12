# Deploy

Guia pra colocar o sistema no ar de graça: banco no **Neon**, API no **Render**,
front no **Vercel**. Os três aceitam login com GitHub.

## 1. Banco de dados (Neon)

1. Cria conta em **neon.tech** (botão "Continue with GitHub").
2. **New Project** → nome `casa-espirita` → região mais perto do Brasil
   (ex: `us-east-1`/aws) → Postgres 17.
3. Na tela do projeto, copia a **Connection string** (algo como
   `postgresql://usuario:senha@ep-xxxx.aws.neon.tech/neondb?sslmode=require`).
   Guarda essa URL -- vai ser usada duas vezes (Render e no seu PC).

## 2. API (Render)

1. Cria conta em **render.com** (login com GitHub) e autoriza o acesso ao
   repositório `sistema-casa-espirita`.
2. **New → Web Service** → escolhe o repositório.
3. Preenche:
   - **Root Directory:** deixa em branco (raiz do repo)
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt && alembic upgrade head && python -m scripts.seed
     ```
   - **Start Command:**
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** Free
4. Em **Environment**, adiciona as variáveis:
   | Nome | Valor |
   |---|---|
   | `DATABASE_URL` | a connection string do Neon (passo 1) |
   | `SECRET_KEY` | gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `APP_ENV` | `production` |
   | `CORS_ORIGINS` | por enquanto `https://localhost` (ajusta no passo 4) |
5. **Create Web Service**. O primeiro deploy demora alguns minutos.
6. Quando terminar, copia a URL que o Render deu (algo como
   `https://sistema-casa-espirita.onrender.com`). Teste abrindo
   `<essa-url>/health` -- deve responder `{"api":"ok","banco":"ok"}`.

> Plano free "dorme" depois de alguns minutos sem uso -- a primeira
> requisição depois disso demora ~30-50s pra acordar. Normal, é o preço do
> gratuito.

### Criar o primeiro usuário admin na base de produção

No seu PC, **uma vez só**, aponta o script pro banco do Neon:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://usuario:senha@ep-xxxx.aws.neon.tech/neondb?sslmode=require"
.\.venv\Scripts\python.exe -m scripts.criar_admin --nome "Seu Nome" --email voce@exemplo.com --senha "escolha-uma-boa"
Remove-Item Env:\DATABASE_URL
```

(o `Remove-Item` no final garante que o terminal volta a usar o `.env` local
depois -- senão os próximos comandos mexeriam sem querer no banco de produção)

## 3. Frontend (Vercel)

1. Cria conta em **vercel.com** (login com GitHub).
2. **Add New → Project** → importa o repositório.
3. Como o front fica em `frontend/`, configura:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (a Vercel geralmente detecta sozinha)
4. Em **Environment Variables**, adiciona:
   | Nome | Valor |
   |---|---|
   | `VITE_API_URL` | `https://sistema-casa-espirita.onrender.com/api/v1` (a URL do Render + `/api/v1`) |
5. **Deploy**. Ao final, a Vercel dá uma URL tipo
   `https://sistema-casa-espirita.vercel.app`.

## 4. Fechar o CORS

Volta no **Render** → Environment → edita `CORS_ORIGINS` pra URL real da Vercel:

```
https://sistema-casa-espirita.vercel.app
```

Salva -- o Render reinicia o serviço sozinho. Pronto: abre a URL da Vercel e
testa o login.

## Atualizações

Depois disso, qualquer `git push` pra `main` já dispara um novo deploy
automático no Render e na Vercel -- não precisa repetir nada disso.
