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
- [ ] Auditoria / LGPD
- [ ] Frontend (React)

## Tecnologias

| Camada | Ferramenta |
|---|---|
| API | Python 3.12 + FastAPI |
| Banco de dados | PostgreSQL 17 |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic |
| Validação | Pydantic v2 |
| Testes | pytest + httpx |
| Frontend | React + Vite *(próxima fase)* |

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
```

## Segurança e LGPD

Dado de religião é dado sensível pela LGPD. O projeto trata isso com:
autenticação por token, autorização por papel, log de auditoria, consentimento
no cadastro, exclusão lógica e rotina de backup. *(implementação em andamento)*

## Licença

MIT — veja [LICENSE](LICENSE).
