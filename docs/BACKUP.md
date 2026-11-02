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
3. **(Recomendado) usuário de banco só de leitura** pro backup. No Neon,
   crie a role `backup_leitura` (Roles → New role) e, no SQL Editor:
   ```sql
   GRANT USAGE ON SCHEMA public TO backup_leitura;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_leitura;
   GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_leitura;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_leitura;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup_leitura;
   ```
4. No GitHub, no repositório → **Settings → Secrets and variables → Actions**:
   - aba **Secrets** → *New repository secret*: `BACKUP_DATABASE_URL` = a
     connection string do Neon (de preferência a do `backup_leitura`);
   - aba **Variables** → *New repository variable*: `BACKUP_AGE_RECIPIENT` =
     a chave pública `age1...`.
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

Pra voltar a produção a partir de um backup (último caso — ver
[PLANO_DE_INCIDENTE.md](PLANO_DE_INCIDENTE.md)): restaure num banco novo do
Neon (ou num *branch*), confira, e troque o `DATABASE_URL` no Render.

## Backup manual

`python -m scripts.backup` (pasta `backups/`, fora do Git) gera um dump **sem
criptografia** no seu computador. Use só se precisar, e apague depois.
