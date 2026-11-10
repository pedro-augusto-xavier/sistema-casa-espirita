# Sistema Casa Espírita

Sistema interno para cadastro de pessoas, atendimentos e tratamentos de uma casa
espírita. Substitui as fichas de papel por um histórico digital, pesquisável e
com controle de acesso.

> Em produção: o sistema é usado no dia a dia de uma casa espírita. Todos os dados do repositório são fictícios.

## Status

Em produção, em uso no dia a dia da casa.

- [x] Esqueleto da API + conexão com o banco
- [x] Modelo de dados (17 tabelas) + migrations
- [x] CRUD de Pessoas (busca, paginação, exclusão lógica) + testes + CI
- [x] Atendimentos (visita avulsa com tratamentos do dia) + listas de referência
- [x] Tratamentos (casos): assistidos, diário de evolução, histórico da pessoa
- [x] Autenticação (JWT) e papéis de usuário (admin / operador)
- [x] Auditoria (quem mexeu em quê) + LGPD (exportar / anonimizar) + backup
- [x] Grupos (Grupo Despertar, Grupo de Estudos): sessão + presença avulsa
- [x] Agenda: eventos (trabalho, palestra, grupo) + escala de trabalhadores
- [x] Frontend (React + Vite + Tailwind): login, pessoas, atendimentos,
      tratamentos com diário, grupos, agenda, edição, usuários e auditoria
      na tela — cobre tudo que a API oferece

## Tecnologias

| Camada | Ferramenta |
|---|---|
| API | Python 3.12 + FastAPI |
| Banco de dados | PostgreSQL 17 |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic |
| Validação | Pydantic v2 |
| Testes | pytest + httpx |
| Frontend | React + Vite + Tailwind CSS + React Router |

## Rodando localmente

Pré-requisitos: Python 3.12+, PostgreSQL 17+ e um banco vazio chamado `casa_espirita`.

```powershell
# 1. Ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Dependências
pip install -r requirements.txt

# 3. Configuração
Copy-Item .env.example .env
# edite o .env com a senha do seu Postgres

# 4. Criar as tabelas
alembic upgrade head

# 5. Popular listas de referência (tipos de tratamento, funções)
python -m scripts.seed

# 6. Criar o primeiro usuário administrador (login é pelo nome, não e-mail)
#    (a senha provisória é gerada e aparece no terminal; vale 72h)
python -m scripts.criar_admin --nome "Seu Nome"

# 7. Subir a API
uvicorn app.main:app --reload
```

Acesse a documentação interativa em `http://127.0.0.1:8000/docs`.

### Autenticação

Todas as rotas de `/api/v1` (menos `/auth/login`) exigem um token.

1. `POST /api/v1/auth/login` com `username` (o **nome** do usuário, não e-mail) e `password` (e `codigo`, pra quem tem verificação em duas etapas) → devolve `access_token`.
2. Envie o token no cabeçalho `Authorization: Bearer <token>` nas demais chamadas.
3. No `/docs` (só em desenvolvimento), clique em **Authorize** e informe nome/senha.

Cada login abre uma **sessão no servidor**: `POST /auth/logout`, trocar a
senha ou desativar o usuário cortam o acesso na hora. A senha criada por um
admin é **provisória** -- no primeiro acesso a pessoa cria a dela (e o admin
configura o código do celular) antes de ver qualquer dado.

Papéis: **operador** faz os cadastros; **admin** faz isso e gerencia usuários,
auditoria, exportação LGPD e anonimização.

### Frontend

Com a API rodando (`http://127.0.0.1:8000`), em outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local   # já vem apontando pra API local
npm run dev
```

Acesse `http://localhost:5173`. Faça login com o usuário administrador criado
no passo 6 acima.

Lint e testes do front:

```powershell
npm run lint
npm run test
```

### Testes e lint

```powershell
pip install -r requirements-dev.txt
ruff check .
pytest
```

Os testes rodam contra o banco do `.env`, cada um dentro de uma transação
que é desfeita no final. O GitHub Actions roda lint + migrations + testes a
cada push (veja `.github/workflows/ci.yml`).

## Estrutura

```
app/
  core/        configuração e conexão com o banco
  models/      tabelas (SQLAlchemy)
  schemas/     formatos de entrada/saída da API (Pydantic)
  api/         rotas, organizadas por versão (v1)
alembic/       migrations do banco
tests/         testes automatizados
frontend/
  src/pages/       telas (login, pessoas, ficha, usuários, auditoria...)
  src/components/  modais e pedaços reutilizáveis (formulário, seletor de pessoa)
  src/auth/        contexto de autenticação e proteção de rota
  src/api/         cliente HTTP que fala com a API
```

## Segurança e LGPD

Dado de religião é dado sensível pela LGPD. Resumo do que o projeto faz
(detalhes, item por item, em [docs/SEGURANCA.md](docs/SEGURANCA.md)):

- **Criptografia AES-256-GCM** de CPF, observações, diário e anexos, com a
  chave fora do banco e do Git, versão de chave e script de rotação. CPF
  achado por **HMAC**; na tela aparece mascarado (`***.456.789-**`).
- **Login** com senha forte (bcrypt), **verificação em duas etapas** (TOTP,
  obrigatória pra admin), **limite de tentativas** por IP e por conta,
  **sessões revogáveis** no servidor.
- **Autorização** por papel, com teste automático garantindo que toda rota
  exige login e que rota de admin recusa operador.
- **Auditoria** imutável (o banco recusa UPDATE/DELETE): logins, falhas,
  edições, CPF visto, exportações -- com IP e sem copiar dado pessoal.
- **Cabeçalhos de segurança** (CSP, HSTS, nosniff, frame-ancestors) na API e
  no site; CORS restrito; erros sem detalhe interno.
- **LGPD**: consentimento com data, exportação dos dados do titular,
  anonimização, política de privacidade em `/privacidade`, registro das
  operações em [docs/LGPD.md](docs/LGPD.md) e
  [plano de incidente](docs/PLANO_DE_INCIDENTE.md).
- **Backup diário** criptografado, guardado 30 dias ([docs/BACKUP.md](docs/BACKUP.md)).
- **CI**: ruff, pip-audit, bandit, npm audit, migrations conferidas com os
  modelos, e Dependabot.

## Deploy

Veja [DEPLOY.md](DEPLOY.md) para o passo a passo (Neon + Render + Vercel,
tudo em plano gratuito).

## Licença

MIT — veja [LICENSE](LICENSE).
