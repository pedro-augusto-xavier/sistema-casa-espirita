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
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
     ```
     (`--proxy-headers` faz o app saber que a conexão original foi HTTPS.
     O IP de quem acessa, usado no limite de tentativas de login e na
     auditoria, vem do cabeçalho `CF-Connecting-IP` da Cloudflare que fica
     na frente do Render -- ver `app/core/contexto.py`.)
   - **Instance Type:** Free
   - **Health Check Path** (em Settings, depois de criar): `/health`. Ele confere
     o banco e se as chaves de criptografia abrem os dados; se falhar, o Render
     não põe a versão nova no ar.
4. Em **Environment**, adiciona as variáveis:
   | Nome | Valor |
   |---|---|
   | `DATABASE_URL` | a connection string do Neon (passo 1) |
   | `SECRET_KEY` | gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `CHAVES_CRIPTOGRAFIA` | gere com `python -m scripts.gerar_chaves` (cifra CPF, observações e anexos) |
   | `CHAVE_HMAC` | sai do mesmo comando acima |
   | `APP_ENV` | `production` |
   | `CORS_ORIGINS` | por enquanto `https://localhost` (ajusta no passo 4) |
   | `MFA_OBRIGATORIO` | opcional: `admin` (padrão), `todos` ou `ninguem` |
   | `MIGRATIONS_DATABASE_URL` | opcional: ver "Usuário do banco com permissão mínima" em [docs/SEGURANCA.md](docs/SEGURANCA.md) |

   O app **não sobe** em produção sem `SECRET_KEY`, `CHAVES_CRIPTOGRAFIA` e
   `CHAVE_HMAC` de verdade -- de propósito. Guarde uma cópia das duas chaves
   de criptografia num gerenciador de senhas: sem elas, os dados cifrados
   (inclusive dos backups) não abrem nunca mais.
5. **Create Web Service**. O primeiro deploy demora alguns minutos.
6. Quando terminar, copia a URL que o Render deu (algo como
   `https://sistema-casa-espirita.onrender.com`). Teste abrindo
   `<essa-url>/health` -- deve responder `{"api":"ok","banco":"ok"}`.

> Plano free "dorme" depois de alguns minutos sem uso -- a primeira
> requisição depois disso demora ~30-50s pra acordar. Normal, é o preço do
> gratuito.

### Criar o primeiro usuário admin na base de produção

O login no sistema é feito pelo **nome** (não e-mail) -- escolha um nome
fácil de lembrar e digitar. No seu PC, **uma vez só**, aponta o script pro
banco do Neon:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://usuario:senha@ep-xxxx.aws.neon.tech/neondb?sslmode=require"
.\.venv\Scripts\python.exe -m scripts.criar_admin --nome "Seu Nome" --senha "escolha-uma-boa"
Remove-Item Env:\DATABASE_URL
```

(`--email` é opcional, só um contato -- pode incluir com `--email voce@exemplo.com` se quiser.)

A senha definida aqui é **provisória**. No primeiro login o sistema pede
pra criar uma senha própria (10+ caracteres) e, como é admin, pra configurar
a verificação em duas etapas com um aplicativo autenticador no celular
(Google Authenticator ou Microsoft Authenticator). Perdeu o celular? Rode o
mesmo comando com `--resetar-mfa`.

(As variáveis `CHAVES_CRIPTOGRAFIA` e `CHAVE_HMAC` também precisam estar no
terminal ao rodar o script contra a produção -- as mesmas do Render.)

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

## 5. Backup diário

Veja [docs/BACKUP.md](docs/BACKUP.md): gerar a chave do backup e cadastrar
dois valores no GitHub. Leva 5 minutos e fica rodando sozinho.

## Atualizações

Depois disso, qualquer `git push` pra `main` já dispara um novo deploy
automático no Render e na Vercel -- não precisa repetir nada disso.

Segurança, LGPD e o que fazer se algo der errado: [docs/SEGURANCA.md](docs/SEGURANCA.md),
[docs/LGPD.md](docs/LGPD.md) e [docs/PLANO_DE_INCIDENTE.md](docs/PLANO_DE_INCIDENTE.md).
