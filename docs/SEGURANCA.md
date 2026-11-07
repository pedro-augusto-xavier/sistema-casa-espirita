# Segurança

Como o sistema protege os dados das pessoas atendidas, item por item do
checklist de segurança. Legenda:

- ✅ **feito no código** (e, quando dá, coberto por teste automático)
- ☁️ **o provedor cuida** (Neon, Render, Vercel, GitHub)
- 👤 **depende de configuração ou de uma decisão** (passo a passo abaixo)
- ➖ **não se aplica** a este sistema (com o motivo)

Documentos relacionados: [LGPD.md](LGPD.md), [PLANO_DE_INCIDENTE.md](PLANO_DE_INCIDENTE.md),
[BACKUP.md](BACKUP.md), [../DEPLOY.md](../DEPLOY.md).

---

## Fase 1 — Urgente

| Item | Situação |
|---|---|
| HTTPS com certificado válido e redirecionamento | ☁️ Vercel e Render emitem e renovam o certificado e redirecionam HTTP → HTTPS (conferido com `curl`). ✅ HSTS nos dois. |
| Porta do banco fechada pra internet | ☁️ O Neon é um banco gerenciado: o endereço é público, mas só aceita conexão com TLS e senha. Restringir por IP (IP Allow) existe só nos planos pagos. 👤 Pra reduzir o estrago se a senha vazar, use o usuário de banco restrito (ver "Usuário do banco com permissão mínima"). |
| Banco sem senha padrão, com senha forte | ☁️ A senha é gerada pelo Neon (aleatória e longa). 👤 Troque quando alguém que tinha acesso sair, ou se ela aparecer em algum lugar indevido (Neon → Roles → Reset password, e atualize o `DATABASE_URL` no Render). |
| Segredos só em variáveis de ambiente; `.env` no `.gitignore` | ✅ `SECRET_KEY`, `DATABASE_URL`, `CHAVES_CRIPTOGRAFIA` e `CHAVE_HMAC` vêm do ambiente. O app **se recusa a subir** em produção com as chaves de exemplo ou mal formatadas (`app/core/config.py`). |
| Histórico do Git sem segredo | ✅ Conferido: o `.env` nunca foi commitado e não há senha nem chave no histórico. 👤 Deixe ligado o *secret scanning* com *push protection* (GitHub → Settings → Code security). |
| Toda rota exige login, menos as públicas de propósito | ✅ Públicas: só `POST /api/v1/auth/login`, `GET /health` e `GET /`. O teste `test_toda_rota_exige_login` percorre **todas** as rotas e quebra o CI se alguma nova aparecer sem proteção. |
| Checagem de permissão no backend (IDOR) | ✅ É um sistema de uma casa só: toda a equipe vê todas as fichas, por desenho — é o trabalho delas. O que é pessoal (sessão, senha, verificação em duas etapas) sempre usa o usuário do token, nunca um id vindo da requisição. Rotas de admin recusam operador (`test_rotas_de_admin_recusam_usuario_comum`). |
| Testar IDOR na mão | ✅ Automatizado: operador tentando virar admin pelo próprio id (`test_operador_nao_se_promove_a_admin`), acessar usuários, auditoria, exportação e anonimização. |
| Debug desligado; erro genérico | ✅ Erro inesperado devolve "Erro interno..." e o detalhe vai só pro log do servidor (`test_erro_interno_devolve_mensagem_generica`). Erro de banco não mostra SQL. Erro de validação não devolve o valor enviado (uma senha recusada não volta na resposta). A documentação `/docs` fica desligada em produção. |

## Fase 2 — Autenticação e contas

| Item | Situação |
|---|---|
| Hash de senha com bcrypt/Argon2 | ✅ bcrypt (biblioteca `bcrypt`). |
| Senha mínima de 10+ e sem senha manjada | ✅ 10 caracteres, pelo menos uma letra, nada de senha comum, nome da pessoa ou nome da casa (`app/core/senhas.py`). Quando o admin cria ou redefine um usuário, o servidor gera uma senha **provisória** aleatória (`secrets`), que aparece uma vez só pro admin e vale 72h. No primeiro acesso a pessoa é obrigada a criar a dela, e aí as regras valem. Vencida, o login com ela é recusado (e sessões abertas com ela caem) até o admin redefinir de novo. |
| Verificação em duas etapas (MFA) | ✅ Código de aplicativo autenticador (TOTP), com proteção contra reuso do mesmo código. **Obrigatória pra admin**; opcional e recomendada pra operador (Minha conta → Ligar). 👤 Pra exigir de todo mundo: `MFA_OBRIGATORIO=todos` no Render. |
| Limite de tentativas no login | ✅ 10 erros em 5 min por IP **e** 5 erros em 5 min por conta (mesmo trocando de IP). Também na troca de senha e na confirmação do código. O IP vem do `CF-Connecting-IP`, que a Cloudflare na frente do Render preenche (`app/core/contexto.py`; outro proxy: `IP_CLIENTE_CABECALHO`). Se o cabeçalho não chegar com um IP válido, o limite por IP fica desligado nessa requisição (e sai um aviso no log) em vez de juntar todo mundo num IP só; o limite por conta continua. O limite por conta não é zerado por quem manda muitos nomes diferentes. 👤 A conferir: que um `CF-Connecting-IP` forjado pelo cliente é trocado pela Cloudflare (a documentação do Render e a da Cloudflare indicam isso, mas não dizem com todas as letras). Teste: um web service temporário no Render, sem banco nem segredos, que só devolve os cabeçalhos recebidos; mandar `CF-Connecting-IP: 192.0.2.123` pelo endereço onrender.com e pelo domínio próprio; conferir que chega o seu IP real; apagar o serviço. |
| Mesma mensagem pra "usuário não existe" e "senha errada" | ✅ E o mesmo tempo de resposta (o hash é calculado mesmo quando o nome não existe). |
| Papéis com o mínimo de acesso | ✅ **operador**: cadastros, atendimentos, tratamentos, agenda. **admin**: isso e mais usuários, auditoria, exportação LGPD e anonimização. |
| Cookies HttpOnly/Secure/SameSite | ➖ O login não usa cookie: o token vai no cabeçalho `Authorization`. Em troca, o site tem uma CSP rígida (só roda script do próprio site) e o token é inútil depois de "Sair" (ver próxima linha). |
| JWT curto + refresh revogável | ✅ Feito com **sessão no servidor**: cada login cria uma sessão no banco, conferida a cada requisição. Dá o mesmo resultado do refresh token revogável (dá pra cortar na hora), com menos peças. Validade: 8 h, ou 30 dias com "Manter conectado". |
| Logout invalida a sessão no servidor | ✅ `POST /auth/logout`. |
| Recuperação de senha | ➖ Não existe "esqueci a senha" por e-mail. Quem esquece pede pro admin, que redefine (o servidor gera uma senha provisória aleatória que vale 72h, e todas as sessões daquela pessoa caem). |
| Trocar senha exige a senha atual | ✅ E derruba as outras sessões abertas. E-mail só o admin muda. |
| Mudança de credencial derruba sessões mesmo com login simultâneo | ✅ **Época de credencial**: trocar ou redefinir a senha, ligar ou desligar a verificação em duas etapas e mudar o papel gravam uma época nova no usuário. Cada sessão guarda a época que valia quando o login conferiu a senha e só vale enquanto ela for a mesma, então um login que leu a senha antiga não escapa da revogação. O login também reconfere o usuário (com trava) antes de abrir a sessão. Quem fez a mudança em si mesmo continua logado naquele aparelho. |
| Remover acesso de quem saiu no mesmo dia | ✅ Desativar o usuário corta o acesso na hora. Reativar não devolve a senha antiga: o servidor gera uma senha provisória nova (vale 72h). 👤 É processo: quem sai da equipe é desativado no mesmo dia (Usuários → Desativar). |

## Fase 3 — Criptografia e chaves

| Item | Situação |
|---|---|
| Lista de campos sensíveis | ✅ Cifrados: **CPF**, **observações** (ficha, atendimento e tratamento do dia), **situação final**, **diário do tratamento**, **arquivos anexados** (com o nome e a descrição de cada um) e o segredo da verificação em duas etapas. Não cifrados, de propósito: nome, telefone e endereço (precisam de busca e aparecem em toda tela) — ficam protegidos pelo controle de acesso e pela criptografia de disco do Neon. |
| AES-256-GCM com biblioteca pronta | ✅ `cryptography` (AESGCM), nonce aleatório por valor, e o nome da coluna amarrado ao dado (um valor copiado de uma coluna pra outra não abre). `app/core/cripto.py`. |
| Chave fora do banco e do repositório | ✅ Variáveis `CHAVES_CRIPTOGRAFIA` e `CHAVE_HMAC` no Render. 👤 Guarde uma cópia num gerenciador de senhas: **sem ela, os dados cifrados — inclusive dos backups — não abrem nunca mais.** |
| Busca e duplicidade de CPF por HMAC | ✅ Coluna `cpf_hash` (HMAC-SHA256, chave separada) com índice único. A busca por CPF funciona com o número completo. Como ela confirma o CPF, achar uma ficha pelo CPF fica na auditoria (`visualizar`, motivo `busca`, entra em "CPFs vistos"), e cada usuário tem 10 buscas por hora de CPF válido que não acham ninguém — senão dava pra testar os 1.000 palpites que sobram da máscara. Telefone de 11 números não passa no dígito verificador e não gasta tentativa. |
| Versão da chave junto do dado | ✅ Cada valor guarda o id da chave que o cifrou. |
| Chave errada no painel | ✅ O `/health` abre uma amostra dos dados com a chave configurada e responde 503 se não conseguir — o Render então não põe a versão nova no ar (Health Check Path = `/health`). |
| Plano de rotação | ✅ Ver "Se a chave vazar", abaixo. Script: `scripts/rotacionar_chaves.py` (testado). |
| Migração reversível | ✅ O CI grava dados no formato antigo num banco descartável, cifra, decifra de volta e cifra de novo, conferindo valor por valor (`tests/verificar_migracoes.py`). O script se recusa a rodar em banco que já tem tabelas. |
| Dados de antes da criptografia | ✅ Em 02/11/2026 o `VACUUM FULL` reescreveu as tabelas e apagou fisicamente as colunas antigas (o Postgres só esconde coluna apagada) e as versões antigas das linhas — conferido. O histórico do Neon guarda 6 h: a versão antiga deixa de existir lá por volta das 03h de 03/11/2026. Não há branches nem snapshots do Neon com dados antigos. |
| Backups criptografados | ✅ O backup diário é cifrado inteiro com `age` (ver [BACKUP.md](BACKUP.md)), e os campos sensíveis já estão cifrados dentro dele. |
| Disco criptografado | ☁️ Neon, Render e Vercel criptografam o armazenamento. |

### Se a chave vazar (rotação)

1. Gere uma chave nova: `python -m scripts.gerar_chaves --rotacao 2`.
2. No Render, `CHAVES_CRIPTOGRAFIA` vira `2:<nova>,1:<antiga>` (a primeira é a que cifra; as outras só leem). Salve e espere o deploy.
3. Recifre tudo com a nova: rode o script apontando pro banco de produção
   (numa linha só, sem salvar a URL em arquivo):
   ```powershell
   $env:DATABASE_URL="<url do Neon>"; $env:APP_ENV="production"; $env:SECRET_KEY="<a do Render>"; $env:CHAVES_CRIPTOGRAFIA="<a do Render>"; $env:CHAVE_HMAC="<a do Render>"; .\.venv\Scripts\python.exe -m scripts.rotacionar_chaves --executar; Remove-Item Env:\DATABASE_URL,Env:\APP_ENV,Env:\SECRET_KEY,Env:\CHAVES_CRIPTOGRAFIA,Env:\CHAVE_HMAC
   ```
4. Rode de novo sem `--executar` e confira que tudo está na chave 2.
5. Tire a chave antiga do Render (`CHAVES_CRIPTOGRAFIA=2:<nova>`).
6. Backups antigos continuam cifrados com a chave velha: guarde-a até eles expirarem (30 dias) e depois descarte.

Se vazar a `CHAVE_HMAC`: gere outra, troque no Render e rode o script com
`--executar --recalcular-hash`. Se vazar a `SECRET_KEY`: troque no Render —
todo mundo é desconectado e entra de novo.

## Fase 4 — Código

| Item | Situação |
|---|---|
| Schema de entrada em toda rota | ✅ Pydantic: tipos, tamanhos e formatos (CPF, CEP, UF, datas, e-mail). |
| Mass assignment | ✅ Campos internos (`id`, `ativo`, `anonimizada`, `papel`...) não passam: são ignorados no cadastro de pessoa e recusados na edição e no cadastro de usuário (testes `test_campos_*`). |
| SQL só com ORM/parâmetros | ✅ SQLAlchemy. SQL escrito à mão só em migrations e no script de rotação, com nomes fixos — nunca com texto vindo de fora (`test_sql_injection_na_busca_nao_faz_nada`). |
| Nada de `dangerouslySetInnerHTML` | ✅ Nenhum no front. O QR code é desenhado pelo React. |
| CSRF | ➖ Sem cookie de sessão, não há CSRF. O CORS só aceita o domínio do site. |
| Upload: tipo pelo conteúdo | ✅ "Números mágicos" (JPEG, PNG, WebP, HEIC, PDF); o que o navegador declara é ignorado. |
| Upload: limite de tamanho | ✅ 8 MB. |
| Upload: fora da pasta do código, nome trocado | ✅ Fica no banco, cifrado, numa tabela própria; o nome original é só uma informação. Não existe pasta de uploads no servidor. |
| Download só autenticado | ✅ E com CSP `sandbox` e `no-store`. |
| API devolve só o necessário | ✅ `response_model` em todas as rotas — hash de senha e segredo da verificação nunca saem. |
| CPF mascarado | ✅ Ficha e listas mostram `***.456.789-**`. O completo só pelo botão "ver", na edição e no PDF — e cada vez fica na auditoria. |
| Exportação com controle | ✅ Exportação LGPD (JSON) só admin; todo PDF gerado fica registrado; todo PDF tem aviso de dado sensível no rodapé. |
| Paginação com limite | ✅ No máximo 100 itens por página (auditoria: 200). |
| HSTS, nosniff, X-Frame-Options | ✅ API (`app/core/security_headers.py`) e site (`frontend/vercel.json`). |
| Content-Security-Policy | ✅ Site: só script do próprio site; conexão só com a API. API: `default-src 'none'`. |
| CORS só pro site | ✅ Só a origem do `CORS_ORIGINS`, sem credenciais, só os métodos e cabeçalhos usados. |

## Fase 5 — Servidor e infraestrutura

| Item | Situação |
|---|---|
| SSH, firewall, atualizações do sistema, fail2ban, app sem root | ➖ Não existe servidor próprio: Render, Vercel e Neon são serviços gerenciados (sem SSH). ☁️ Eles cuidam do sistema operacional, do firewall e das atualizações. |
| Usuário do banco com permissão mínima | 👤 Opcional e recomendado — ver abaixo. A API roda com `app_casa`; as migrations rodam fora do Render, no workflow de deploy, com a URL do dono num segredo do GitHub. |
| Cloudflare na frente | ☁️ O Render já fica atrás da Cloudflare; a Vercel tem rede própria com proteção contra DDoS. |
| Painéis administrativos fechados | ✅ `/docs` desligado em produção. 👤 O DBeaver conecta direto no Neon: só no seu computador, com a senha guardada no gerenciador. |
| Ambientes separados | ✅ Desenvolvimento usa banco local e chaves de exemplo — que a produção recusa. 👤 Não copie dados reais pro banco local. |
| MFA nas contas que controlam tudo | 👤 Ligue a verificação em duas etapas no **GitHub, Render, Vercel, Neon e no e-mail** usado neles. Quem entra nessas contas tem acesso a tudo. |

### Usuário do banco com permissão mínima (opcional)

Sem isso, o app usa o usuário dono do banco (pode criar e apagar tabelas).
Com um usuário restrito, quem invadir o app não consegue apagar tabelas nem
mexer na auditoria — nem desligar o trigger que a protege. Isso só vale se
a URL do dono **não estiver no Render**: tudo que está no Environment do
serviço chega ao processo da API, e quem invadir o app leria a variável.
Por isso as migrations rodam no workflow de deploy do GitHub (ver
[DEPLOY.md](../DEPLOY.md)), e a URL do dono fica só no gerenciador de senhas
e no segredo `DONO_DATABASE_URL` do Environment `producao` do GitHub.

1. No Neon (Roles → New role), crie `app_casa` e copie a senha.
2. No SQL Editor do Neon, como dono do banco:
   ```sql
   GRANT USAGE ON SCHEMA public TO app_casa;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_casa;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_casa;
   -- auditoria: só ler e inserir
   REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_casa;
   -- o que as migrations criarem no futuro também vale pro app_casa
   ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_casa;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT USAGE, SELECT ON SEQUENCES TO app_casa;
   ```
3. No Render, `DATABASE_URL` = a URL com `app_casa` e a senha nova
   (`python -m scripts.senha_do_app` gera e imprime). A URL do dono vai pro
   segredo `DONO_DATABASE_URL` do GitHub, **nunca** pro Render.

## Fase 6 — Logs, backup e incidente

| Item | Situação |
|---|---|
| Registrar logins, permissões, dado completo visto, exportações, exclusões (quem, o quê, quando, IP) | ✅ Tudo na tabela `audit_log`, com IP. Tela: **Auditoria** (só admin), com filtro por ação. |
| Logs sem senha, token ou CPF | ✅ A auditoria guarda **quais** campos mudaram, não os valores (CPF, endereço e observações não viram cópia no log). Falha de login não guarda o que foi digitado. O log de acesso do servidor corta a busca da URL (`?q=` pode ser um CPF). |
| Logs que o app não consegue apagar | ✅ O banco recusa UPDATE, DELETE e TRUNCATE na auditoria (trigger). Com o usuário restrito acima (e a URL do dono fora do Render), nem desligar o trigger dá. Cópia fora do servidor: vai junto no backup diário. |
| Alerta pra coisa estranha | ✅ Bolinha vermelha em "Auditoria" pro admin quando há 10+ logins errados em 24 h ou acesso entre 23 h e 6 h; resumo no topo da tela. |
| Backup diário, em outro lugar, criptografado, 30 dias | ✅ Workflow `.github/workflows/backup.yml`. 👤 Precisa ser ligado uma vez: [BACKUP.md](BACKUP.md). |
| Testar a restauração | 👤 A cada 3 meses, roteiro em [BACKUP.md](BACKUP.md). |
| Plano de incidente | ✅ [PLANO_DE_INCIDENTE.md](PLANO_DE_INCIDENTE.md). 👤 Preencher os contatos. |

## Fase 7 — LGPD

Ver [LGPD.md](LGPD.md): inventário de dados, bases legais, dados sensíveis,
retenção, terceiros, direitos do titular e encarregado. A política de
privacidade fica no próprio sistema, em `/privacidade` (link na tela de login
e em "Minha conta"). 👤 Vale uma revisão jurídica, e a casa precisa decidir
alguns pontos (estão marcados no documento).

## Fase 8 — Manutenção e testes

| Item | Situação |
|---|---|
| Dependabot | ✅ `.github/dependabot.yml` (Python, front e GitHub Actions, toda segunda). 👤 Ligue também os *Dependabot alerts* em Settings → Code security. |
| `pip-audit` / `npm audit` no CI | ✅ A cada push. |
| Secret scanning | 👤 Settings → Code security → Secret scanning + Push protection. |
| Análise estática | ✅ Bandit no CI (`bandit -r app scripts -ll`). |
| Testes de "pentest básico" | ✅ Automatizados em `tests/test_seguranca.py`: rota sem login, usuário comum em rota de admin, troca de id, campos extras, `' OR 1=1 --`, `<script>`, erro forçado, limite de tentativas, senha fraca, verificação em duas etapas. |
| Scanner automático (OWASP ZAP) | 👤 Opcional, num ambiente de teste — nunca em produção com dados reais. |
| securityheaders.com e SSL Labs | 👤 Depois do deploy: [securityheaders.com](https://securityheaders.com/?q=https://sistema-casa-espirita.vercel.app) e [SSL Labs](https://www.ssllabs.com/ssltest/analyze.html?d=sistema-casa-espirita.vercel.app). |

### Rotina

- **Todo mês:** aceitar (ou revisar) os PRs do Dependabot; olhar a tela de Auditoria (filtro "Login falhou" e o resumo do topo).
- **A cada 3 meses:** testar a restauração de um backup ([BACKUP.md](BACKUP.md)); revisar quem tem acesso (tela Usuários: quem não entra há muito tempo ou já saiu da equipe → desativar).
- **Todo ano:** reler este documento, a política de privacidade e o plano de incidente.
