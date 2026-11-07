# Backup

Todo dia, às 03:17 (horário de Brasília), o GitHub Actions faz uma cópia do
banco de produção, compacta, **criptografa** e guarda por **30 dias** — num
provedor diferente do Neon. Workflow: `.github/workflows/backup.yml`.

A criptografia usa o [`age`](https://age-encryption.org) com **chave
pública**: o GitHub só tem a chave que fecha. A que abre fica com você, fora
de qualquer servidor. Mesmo que alguém baixe o arquivo, não consegue ler.

> O Neon também guarda um histórico próprio (restauração para um ponto no
> tempo), mas por poucas horas/dias, dependendo do plano. O backup diário
> cobre o resto e protege contra perder a conta do Neon.

## Ligar (uma vez)

1. **Instale o age** no Windows: `winget install FiloSottile.age`
   (feche e abra o terminal depois).
2. **Gere o par de chaves:**
   ```powershell
   age-keygen -o chave-backup-casa.txt
   ```
   Ele mostra `Public key: age1...` — essa é a **chave pública** (pode ser
   vista por qualquer um). O arquivo `chave-backup-casa.txt` é a **chave
   privada**: guarde no gerenciador de senhas e/ou num pendrive guardado na
   casa, e apague do computador. **Nunca** no Git. Sem ela, nenhum backup
   abre.
3. **(Recomendado) usuário de banco só de leitura** pro backup. Crie a role
   **por SQL**, nunca pelo painel (Roles → New role): role criada pelo
   painel ganha `neon_superuser`, que escreve em tudo. Gere a senha no
   gerenciador de senhas (24+ caracteres, só letras e números, pra não
   precisar escapar na URL). No SQL Editor, logado com o **mesmo usuário
   dono** que as migrations usam (o do `DONO_DATABASE_URL`) — senão os
   `ALTER DEFAULT PRIVILEGES` não valem pras tabelas novas:
   ```sql
   CREATE ROLE backup_leitura WITH LOGIN PASSWORD '<senha>';
   GRANT USAGE ON SCHEMA public TO backup_leitura;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_leitura;
   GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_leitura;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_leitura;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup_leitura;
   ```
   Confira (as duas devem dar `false`):
   ```sql
   SELECT pg_has_role('backup_leitura', 'neon_superuser', 'member'),
          has_table_privilege('backup_leitura', 'pessoa', 'INSERT');
   ```
4. No GitHub, no repositório → **Settings → Environments → New
   environment** `backup`:
   - *Deployment branches and tags* → **Selected branches** → `main`.
     **Sem** *Required reviewers* (roda de madrugada, ninguém aprova);
   - *Environment secrets* → `BACKUP_DATABASE_URL` = a connection string do
     `backup_leitura`, **sem pooling** (no *Connect* do Neon, desligue
     *Connection pooling*: o host não pode ter `-pooler`);
   - *Environment variables* → `BACKUP_AGE_RECIPIENT` = a chave pública
     `age1...`.

   Sem um dos dois, o workflow falha (fica vermelho) em vez de passar.
5. **Teste:** Actions → *Backup do banco* → *Run workflow*. Deve terminar
   verde, com um artefato `backup-...` no fim da página.

Repositório parado por 60 dias faz o GitHub pausar workflows agendados. Dê
uma olhada em Actions uma vez por mês (a rotina de segurança já inclui isso).

## Restaurar (e testar a cada 3 meses)

Teste num banco **local**, nunca por cima da produção sem necessidade.

1. Actions → *Backup do banco* → abra uma execução → baixe o artefato (vem
   um `.zip`) e extraia o `.sql.gz.age`.
2. No **Git Bash**, na pasta do arquivo:
   ```bash
   age -d -i /caminho/chave-backup-casa.txt casa-espirita-AAAAMMDD-HHMM.sql.gz.age | gzip -d > backup.sql
   ```
3. Crie um banco vazio e restaure (use um PostgreSQL atualizado: o `psql`
   precisa ser 17.6+ ou 16.10+ pra entender o arquivo gerado pelo `pg_dump` 18):
   ```bash
   createdb -U postgres restauracao_teste
   psql -U postgres -d restauracao_teste -f backup.sql
   ```
4. Confira: `psql -U postgres -d restauracao_teste -c "select count(*) from pessoa"`
   deve bater com o sistema. CPF, observações e anexos continuam cifrados no
   banco restaurado: pra ler pelo sistema, rode a API apontando pra ele com
   as **mesmas** `CHAVES_CRIPTOGRAFIA` e `CHAVE_HMAC` da produção.
5. Apague tudo depois: `dropdb -U postgres restauracao_teste` e o
   `backup.sql` (ele está aberto, sem criptografia).

## Voltar a produção a partir de um backup

O banco guarda também quem pode entrar: senhas, verificação em duas etapas,
papéis, contas desativadas e sessões abertas. Restaurar o banco **inteiro**
devolve tudo isso como estava no backup, ou seja, um acesso cortado depois
dele (conta desativada, senha vazada e redefinida, celular perdido com o MFA
zerado, admin rebaixado, sessão encerrada) **volta a valer**. Por isso há
dois caminhos. Escolha pelo que aconteceu:

| Aconteceu | Caminho |
|---|---|
| Alguns dados foram apagados ou alterados | **1. Seletivo**: produção continua no ar |
| O banco se perdeu ou ficou corrompido | **2. Banco inteiro**: último caso |

**Nunca** use `pg_restore --clean` (ou `psql -f` do backup) por cima do banco
de produção.

### 1. Seletivo (dado apagado ou alterado)

1. Restaure o backup num banco **à parte**, como no roteiro de teste acima
   (local) ou num *branch* do Neon no ponto no tempo de antes do problema.
2. Copie de lá **só as linhas que precisa** das tabelas de dados (`pessoa`,
   `atendimento`, `tratamento`, `anexo`...). Ex.: no banco à parte,
   `\copy (SELECT * FROM pessoa WHERE id IN (...)) TO 'linhas.csv' CSV`; na
   produção, `\copy pessoa FROM 'linhas.csv' CSV`. Os campos cifrados vêm
   cifrados e continuam legíveis (as chaves são as mesmas).
3. **Proibido copiar `usuario`, `sessao_usuario` e `audit_log`.** As duas
   primeiras trariam de volta acessos já revogados, e a auditoria não pode
   ser reescrita.
4. Apague o banco à parte e os arquivos `.csv`/`backup.sql` (estão abertos).

### 2. Banco inteiro (perda total ou corrupção)

O sistema fica **fora do ar** do passo 1 ao 7 (minutos até uma hora).
Anote o horário de cada passo (vai pro registro do incidente).

1. **Render** → o serviço → *Suspend*.
2. **Anote o horário do backup em UTC.** No artefato do GitHub, ele está no
   nome (`casa-espirita-AAAAMMDD-HHMM`, já em UTC). No Neon, é o ponto no
   tempo escolhido: some 3h ao horário de Brasília.
3. **Restaure:**
   - **A. Histórico do Neon** (se o ponto ainda estiver na janela do plano):
     restaure o *branch* para o ponto no tempo. O Neon guarda o estado de
     antes da restauração num *branch* à parte (confira em *Branches*):
     esse é o **banco antigo** do passo 4.
   - **B. Artefato do GitHub**: decifre como no roteiro de teste (passos 1
     e 2) e restaure num banco **novo** do Neon:
     `psql "<url do banco novo>" -f backup.sql`. Se o banco que se perdeu
     ainda abrir, ele é o **banco antigo** do passo 4.
   - Se o app usa o usuário restrito `app_casa`, refaça os `GRANT` de
     [SEGURANCA.md](SEGURANCA.md) ("Usuário do banco com permissão mínima")
     no banco restaurado: o backup não leva permissões.
4. **Refaça as revogações**, no PowerShell, na pasta do projeto. Primeiro
   sem `--executar` (só mostra o que faria):
   ```powershell
   $env:DATABASE_URL="<url do banco restaurado>"
   .\.venv\Scripts\python.exe -m scripts.pos_restauracao --banco-antigo "<url do banco antigo>" --desde "AAAA-MM-DD HH:MM"
   ```
   - Sem banco antigo (não abre mais), troque
     `--banco-antigo "..." --desde "..."` por `--sem-banco-antigo`: **todas**
     as contas ativas recebem senha provisória nova e MFA zerado.
   - Com banco antigo, ele lista a auditoria de usuários desde o backup
     (desativações, senhas redefinidas, MFA zerado, papel mudado...) e o
     que vai mudar em cada conta: desativado num dos dois → desativado;
     papel → o menor; senha ou MFA diferentes → senha provisória nova e MFA
     zerado.
   - Em qualquer caso, **todas as sessões são encerradas**.

   Conferiu? Rode de novo com `--executar` no fim e digite o nome do banco
   pra confirmar. **Copie** as senhas provisórias e as duas linhas
   `SECRET_KEY=...` e `SESSOES_VALIDAS_DESDE=...` que ele mostra. Depois:
   `Remove-Item Env:\DATABASE_URL`.
5. **Render** → *Environment*: `DATABASE_URL` = o banco restaurado (se
   mudou), `SECRET_KEY` e `SESSOES_VALIDAS_DESDE` com os valores do passo
   4. Salve. A chave nova e a data invalidam todo token emitido antes, mesmo
   que alguma sessão do banco restaurado tenha escapado.
6. **Render** → *Resume*. Confira que a tela de login funciona.
7. **Sua conta**: entre com a senha provisória que o script mostrou e
   configure de novo a verificação em duas etapas. Se não der,
   `python -m scripts.criar_admin --nome "..." --resetar-mfa` apontando pro
   banco restaurado (ver DEPLOY.md).
8. **Repasse as senhas provisórias** a cada pessoa, pessoalmente ou por um
   canal seguro. Elas valem 72h. Depois disso, o admin redefine.
9. **Dados que se perderam**: refaça as anonimizações feitas depois do
   backup ([LGPD.md](LGPD.md)) e, pela auditoria do banco antigo, o que mais
   precisar.
10. **Não apague o banco antigo** até fechar o incidente (é prova). Apague o
    `backup.sql` (está aberto).

`SESSOES_VALIDAS_DESDE` pode ficar no Render depois disso: data passada não
atrapalha ninguém que entrou depois dela.

## Backup manual

`python -m scripts.backup` (pasta `backups/`, fora do Git) gera um dump **sem
criptografia** no seu computador. Use só se precisar, e apague depois.
