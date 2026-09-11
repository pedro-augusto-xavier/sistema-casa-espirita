# Sistema Casa Espírita

Sistema interno para cadastro de pessoas, atendimentos e tratamentos de uma casa
espírita. Substitui as fichas de papel por um histórico digital, pesquisável e
com controle de acesso.

> Projeto de estudo / portfólio. Todos os dados do repositório são fictícios.

## Status

Em desenvolvimento.

- [x] Esqueleto da API + conexão com o banco
- [x] Modelo de dados (17 tabelas) + migrations
- [x] CRUD de Pessoas (busca, paginação, exclusão lógica) + testes + CI
- [x] Atendimentos (visita avulsa com tratamentos do dia) + listas de referência
- [x] Tratamentos (casos): assistidos, diário de evolução, histórico da pessoa
- [x] Autenticação (JWT) e papéis de usuário (admin / operador)
- [x] Auditoria (quem mexeu em quê) + LGPD (exportar / anonimizar) + backup
- [x] Frontend (React + Vite + Tailwind): login, pessoas, atendimentos,
      tratamentos com diário, edição, usuários e auditoria na tela

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

# 6. Criar o primeiro usuário administrador
python -m scripts.criar_admin --nome "Seu Nome" --email voce@exemplo.com --senha "trocar-depois"

# 7. Subir a API
uvicorn app.main:app --reload
```

Acesse a documentação interativa em `http://127.0.0.1:8000/docs`.

### Autenticação

Todas as rotas de `/api/v1` (menos `/auth/login`) exigem um token.

1. `POST /api/v1/auth/login` com `username` (e-mail) e `password` → devolve `access_token`.
2. Envie o token no cabeçalho `Authorization: Bearer <token>` nas demais chamadas.
3. No `/docs`, clique em **Authorize** e informe e-mail/senha.

Papéis: **operador** faz os cadastros; **admin** faz isso e gerencia usuários
(`/api/v1/usuarios`).

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

Dado de religião é dado sensível pela LGPD. O projeto trata isso com:

- **Autenticação** por token JWT; **autorização** por papel (admin / operador).
- **Senha** com hash bcrypt (nunca em texto puro).
- **Auditoria**: cada criação/edição/exclusão e cada login vira uma linha em
  `audit_log` (quem, o quê, quando, o que mudou). Consulta em
  `GET /api/v1/auditoria` (só admin).
- **Consentimento** registrado no cadastro, com data.
- **Direito de acesso**: `GET /api/v1/pessoas/{id}/exportar` devolve tudo que o
  sistema guarda sobre a pessoa.
- **Direito ao esquecimento**: `POST /api/v1/pessoas/{id}/anonimizar` apaga os
  dados pessoais e mantém só a linha, para o histórico de atendimentos não
  ficar órfão.
- **Exclusão lógica** (soft delete) em vez de apagar na hora.
- **Backup**: `python -m scripts.backup` gera um dump restaurável em `backups/`.

## Licença

MIT — veja [LICENSE](LICENSE).
