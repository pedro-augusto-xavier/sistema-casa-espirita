# Mudanças

O que muda em cada versão. Formato inspirado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em
[SemVer](https://semver.org/lang/pt-BR/) (API, front e `pyproject.toml`
andam juntos).

## [1.0.0] — 2026-11-11

Primeira versão numerada. O sistema já estava em produção, em uso no dia a
dia da casa.

### O que o sistema faz

- Fichas de pessoas: busca, paginação, desativar/reativar, arquivos anexos.
- Atendimentos (visita com os tratamentos do dia) e tratamentos em casos,
  com assistidos e diário de evolução.
- Grupos (sessão + presença) e agenda com escala de trabalhadores.
- Usuários admin/operador, login pelo nome, senha provisória de 72h e
  verificação em duas etapas (obrigatória pra admin).
- Auditoria imutável, LGPD (exportar/anonimizar), campos sensíveis
  criptografados e backup diário criptografado.

### Novo nesta versão

- Teste de ponta a ponta (Playwright) no CI: entrar, cadastrar ficha e
  registrar atendimento num navegador; o deploy depende dele.
- Monitor a cada 10 min (API + site), com aviso por e-mail se cair.
- Erro inesperado numa tela mostra aviso com "Recarregar" em vez de página
  em branco.
- Manual do voluntário ([docs/MANUAL.md](docs/MANUAL.md)).

### Segurança

- `APP_ENV` passou a ser obrigatório: sem ele a API não sobe, em vez de
  subir em modo de desenvolvimento com as travas de produção desligadas.
