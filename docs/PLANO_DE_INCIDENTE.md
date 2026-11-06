# Plano de resposta a incidente

Pra seguir com calma se algo der errado: senha vazada, acesso estranho na
auditoria, computador com o sistema aberto perdido, banco exposto. Foi
escrito antes de precisar justamente pra não ter que pensar na hora.

> **Incidente de segurança** (LGPD): qualquer acesso não autorizado, perda,
> vazamento ou alteração indevida de dado pessoal — mesmo que pareça pequeno.

## 1. Quem faz o quê

👤 Preencha e mantenha atualizado.

| Papel | Quem | Contato |
|---|---|---|
| Decide (fala pela casa, comunica titulares e ANPD) | _coordenação da casa_ | _telefone_ |
| Executa (parte técnica) | _Pedro Augusto Xavier_ | _telefone / e-mail_ |
| Substituto técnico | _a definir_ | |

## 2. Primeiras horas: conter

Faça na ordem. Anote a hora de cada passo (vai pro registro).

1. **Cortar o acesso de quem não devia.**
   - Conta da equipe comprometida: tela **Usuários** → *Desativar* (derruba as sessões na hora) ou *Desconectar* + *Redefinir senha*.
   - Não dá pra entrar como admin: `python -m scripts.criar_admin --nome "..." --resetar-mfa` (mostra a senha provisória gerada) apontando pro banco de produção (ver DEPLOY.md).
2. **Derrubar todas as sessões de todo mundo**, se não souber qual conta foi: troque a `SECRET_KEY` no Render (`python -c "import secrets; print(secrets.token_hex(32))"`). Todos os tokens deixam de valer.
   - Alternativa sem gerar chave: no Render, `SESSOES_VALIDAS_DESDE` = a data e hora de agora em UTC (ex.: `2026-11-06T22:00:00Z`). Todo token emitido antes dela deixa de valer.
3. **Tirar o sistema do ar**, se o ataque estiver em andamento: Render → o serviço → *Suspend*. (A Vercel continua mostrando a tela de login, mas sem a API nada funciona.)
4. **Trocar as senhas e chaves** que podem ter vazado:
   - senha do banco no Neon (Roles → Reset password) → atualizar `DATABASE_URL` no Render (e o secret `BACKUP_DATABASE_URL` no GitHub);
   - chaves de criptografia: roteiro "Se a chave vazar" em [SEGURANCA.md](SEGURANCA.md);
   - senhas e verificação em duas etapas das contas GitHub, Render, Vercel, Neon e do e-mail.
5. **Não apagar nada.** Auditoria, logs do Render e backups são a prova do que aconteceu.

## 3. Descobrir o que vazou e de quem

- **Auditoria** (só admin): filtrar por *Login falhou*, *Entrou*, *Viu dado completo* e *Exportou*; olhar IP, horário e usuário. O resumo no topo mostra o que fugiu do normal.
- **Logs do Render** (Logs, últimos dias): requisições e erros.
- **Neon** (Monitoring): conexões fora do comum ao banco.
- **GitHub**: se algum segredo foi parar no repositório, o *secret scanning* avisa; confira também *Security → Secret scanning alerts*.
- Responda por escrito: **quais dados** (nome? CPF? observações? anexos?), **de quantas e quais pessoas**, **desde quando**, **como** e **se ainda está acontecendo**.

Lembrete: CPF, observações, diário e anexos ficam cifrados no banco. Se
vazou só uma cópia do banco **sem** as chaves (que ficam no Render), esses
campos continuam ilegíveis — isso reduz o risco, mas nome, telefone e
endereço ficam expostos.

## 4. Comunicar

- **ANPD e titulares:** quando o incidente puder trazer **risco ou dano relevante** às pessoas, a casa comunica a Autoridade Nacional de Proteção de Dados e as pessoas afetadas em até **3 dias úteis** a partir de quando ficou sabendo (Resolução CD/ANPD nº 15/2024). Dado sensível (convicção religiosa, saúde) pesa a favor de comunicar.
  - Formulário: [gov.br/anpd](https://www.gov.br/anpd) → "Comunicação de incidente de segurança".
  - Pras pessoas: linguagem simples — o que aconteceu, quais dados, o que a casa fez e o que a pessoa pode fazer.
- Na dúvida, procure orientação jurídica antes do prazo acabar.

## 5. Registrar (sempre — mesmo sem comunicar)

A casa guarda um registro de **todo** incidente, comunicado ou não, por pelo
menos 5 anos. Copie e preencha:

```
Data/hora em que soubemos:
Como soubemos:
O que aconteceu:
Dados envolvidos:
Pessoas afetadas (quantas / quais):
Medidas tomadas (com horário):
Comunicado à ANPD? (sim/não, data, por quê):
Comunicado aos titulares? (sim/não, data, como):
O que muda pra não acontecer de novo:
Responsável pelo registro:
```

## 6. Depois

- Restaurar o que foi alterado/apagado a partir do backup, se precisar: **só as linhas** que precisa, sem nunca copiar `usuario`, `sessao_usuario` e `audit_log` (roteiro "1. Seletivo" em [BACKUP.md](BACKUP.md)). Restaurar o banco **inteiro** devolve os acessos que você acabou de cortar: só em perda total, e seguindo o roteiro "2. Banco inteiro" (inclui refazer as revogações com `scripts.pos_restauracao`).
- Revisar quem tem acesso e o que falhou; atualizar este plano.
