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
     pip install -r requirements.txt
     ```
     (As migrations e o seed **não** rodam aqui: rodam no GitHub, antes do
     deploy -- ver "Atualizações" no fim. Tudo que está no Environment do
     Render chega ao processo da API, e a migration precisa da URL do dono
     do banco.)
   - **Start Command:**
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
     ```
     (`--proxy-headers` faz o app saber que a conexão original foi HTTPS.
     O `'*'` é o mesmo valor que o Render já põe em `FORWARDED_ALLOW_IPS`
     no Python -- não restrinja: os IPs do balanceador do Render não são
     publicados, e restringir faria todo mundo aparecer com o mesmo IP.
     O IP de quem acessa, usado no limite de tentativas de login e na
     auditoria, vem do cabeçalho `CF-Connecting-IP` da Cloudflare que fica
     na frente do Render (variável `IP_CLIENTE_CABECALHO`, não precisa
     mexer) -- ver `app/core/contexto.py`.)
   - **Instance Type:** Free
   - **Health Check Path** (em Settings, depois de criar): `/health`. Ele confere
     o banco e se as chaves de criptografia abrem os dados; se falhar, o Render
     não põe a versão nova no ar.
   - **Auto-Deploy** (em Settings → Build & Deploy): **Off**. Quem dispara o
     deploy é o workflow do GitHub, depois das migrations.
   - **Deploy Hook** (mesma tela): copie a URL -- ela vira o segredo
     `RENDER_DEPLOY_HOOK_URL` no GitHub ("Atualizações", no fim). Quem tem
     essa URL consegue fazer deploy: trate como senha.
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

   Recomendado: em vez da URL do dono, `DATABASE_URL` com o usuário restrito
   `app_casa` -- ver "Usuário do banco com permissão mínima" em
   [docs/SEGURANCA.md](docs/SEGURANCA.md). A URL do dono do banco **nunca**
   fica no Render.

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
.\.venv\Scripts\python.exe -m scripts.criar_admin --nome "Seu Nome"
Remove-Item Env:\DATABASE_URL
```

(`--email` é opcional, só um contato -- pode incluir com `--email voce@exemplo.com` se quiser.)

O script gera a senha e mostra uma vez só no terminal: anote na hora. Ela é
**provisória** e vale 72h. No primeiro login o sistema pede
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

A **Vercel** publica o front sozinha a cada `git push` pra `main`. A **API**
passa pelo job `deploy` do workflow de CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)):

1. push na `main` → o CI roda (testes, lint, auditoria de dependências);
2. com o CI verde, o job `deploy` **espera a sua aprovação**: GitHub →
   Actions → o run do commit → *Review deployments* → `producao` → *Approve*;
3. aprovado, ele roda `alembic upgrade head` e o seed no banco de produção,
   com a URL do dono;
4. e chama o deploy hook do Render pra publicar **exatamente aquele commit**.
   O Render só troca a versão no ar quando a nova passa no `/health`.

**Aprove logo depois do push.** Enquanto você não aprova, o front novo já
está no ar com a API antiga -- se o commit mexeu nos dois lados, o front
pode chamar algo que a API ainda não tem. Se der dois pushes seguidos, basta
aprovar o mais recente: ele leva as migrations dos dois. (Um run antigo
aprovado depois não publica nada: o job só chama o Render se o commit ainda
for o último da `main`.)

O workflow termina quando chama o hook; acompanhe o deploy em si pelo painel
(ou e-mail) do Render.

### Configurar uma vez (GitHub)

Repositório → **Settings → Environments → New environment** → `producao`:

- **Required reviewers:** você. **Não** marque *Prevent self-review* (senão
  ninguém consegue aprovar o seu próprio push).
- **Deployment branches and tags:** *Selected branches and tags* → `main`.
- **Environment secrets:**

  | Nome | Valor |
  |---|---|
  | `DONO_DATABASE_URL` | URL do dono do banco (`neondb_owner`) -- a do Neon, passo 1 |
  | `CHAVES_CRIPTOGRAFIA` | a mesma do Render |
  | `CHAVE_HMAC` | a mesma do Render |
  | `RENDER_DEPLOY_HOOK_URL` | o Deploy Hook do Render (passo 2) |

As chaves de criptografia vão junto porque algumas migrations cifram dados
(e o job roda com `APP_ENV=production`, que recusa as chaves de exemplo:
sem elas a migration falha, em vez de cifrar dado real com chave pública).
A `SECRET_KEY` de verdade **não** vai: o job gera uma descartável.

O log do Actions deste repositório é **público**. Os segredos aparecem como
`***`, e o job também esconde a senha e cada chave sozinhas. Ao mexer no
job: nada de `set -x`, `echo` de variável ou `${{ secrets.X }}` dentro do
script -- segredo só por `env:` do passo.

### Regra pras migrations

Entre a migration rodar e o código novo entrar no ar, o código **antigo**
continua atendendo (minutos, ou mais se o deploy falhar). Então a migration
não pode quebrar o código que está no ar:

- acrescentar tabela, coluna que aceita vazio ou com padrão: pode, num
  deploy só;
- apagar ou renomear coluna/tabela, ou tornar obrigatória: em **dois**
  deploys -- primeiro o código para de usar, depois a migration remove.

### Plano B: rodar do seu PC (GitHub Actions fora do ar)

No PowerShell, na pasta do projeto (URL do dono e chaves do gerenciador de
senhas):

```powershell
$env:APP_ENV = "production"
$env:DATABASE_URL = "<URL do dono do banco>"
$env:CHAVES_CRIPTOGRAFIA = "<a mesma do Render>"
$env:CHAVE_HMAC = "<a mesma do Render>"
$env:SECRET_KEY = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
Remove-Item Env:\APP_ENV, Env:\DATABASE_URL, Env:\CHAVES_CRIPTOGRAFIA, Env:\CHAVE_HMAC, Env:\SECRET_KEY
```

Depois, no Render: **Manual Deploy → Deploy latest commit**. (O
`Remove-Item` garante que o terminal volta a usar o `.env` local -- senão os
próximos comandos mexeriam no banco de produção.)

Segurança, LGPD e o que fazer se algo der errado: [docs/SEGURANCA.md](docs/SEGURANCA.md),
[docs/LGPD.md](docs/LGPD.md) e [docs/PLANO_DE_INCIDENTE.md](docs/PLANO_DE_INCIDENTE.md).
