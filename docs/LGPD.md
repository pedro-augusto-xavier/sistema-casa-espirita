# LGPD — registro das operações de tratamento

O que o sistema guarda, pra quê, com qual base legal, onde e por quanto tempo.
É o "registro das operações" que a LGPD (art. 37) pede, e serve de base pra
política de privacidade que aparece no sistema (`/privacidade`).

> Isto é o lado técnico e organizacional. Não substitui orientação
> jurídica: os pontos marcados com 👤 são **decisões da casa** e valem uma
> revisão com advogado(a).

## Quem é quem

| Papel (LGPD) | Quem |
|---|---|
| Controlador | Casa Espírita Amor e Perdão — Nova Friburgo/RJ. 👤 CNPJ: ______ |
| Operadores (processam em nome da casa) | Neon (banco de dados), Render (servidor da API), Vercel (site), GitHub (código e cópias de segurança criptografadas) |
| Quem desenvolve e mantém o sistema | Pedro Augusto Xavier (voluntário) |
| Encarregado (DPO) | 👤 Ver "Encarregado" abaixo |

## Inventário dos dados

| Dados | Exemplos | Pra quê | Base legal (proposta) | Onde | Quanto tempo |
|---|---|---|---|---|---|
| Identificação | nome, nascimento, sexo, estado civil, nº de filhos | identificar a pessoa e organizar o atendimento | consentimento (art. 7º, I) | Neon | enquanto houver vínculo com a casa ou até pedido de exclusão (👤 ver Retenção) |
| Contato | telefone, endereço, CEP | falar com a pessoa sobre os atendimentos | consentimento (art. 7º, I) | Neon | idem |
| CPF (opcional) | — | evitar ficha duplicada | consentimento (art. 7º, I) | Neon, **cifrado** | idem |
| Atendimentos e tratamentos espirituais | datas, tipos, quem atendeu, observações, diário | acompanhar o tratamento | **dado sensível** — consentimento específico e destacado (art. 11, I) | Neon; observações e diário **cifrados** | idem |
| Pessoas ligadas a um tratamento | filhos, pais, cônjuge por quem alguém pediu atendimento, e o vínculo | organizar o tratamento a pedido do responsável | **dado sensível** — 👤 ver "Assistidos e menores" | Neon | idem |
| Fotos e documentos | foto de documento, exame, carta | guardar o que a pessoa entregou | consentimento (art. 11, I) | Neon, **cifrado** | idem |
| Usuários do sistema (equipe) | nome, e-mail opcional, hash da senha, segredo da verificação em duas etapas (cifrado) | controlar o acesso | execução das atividades da casa / legítimo interesse (art. 7º, IX) | Neon | enquanto fizer parte da equipe; depois fica desativado (a auditoria precisa saber quem fez o quê) |
| Registros de acesso e auditoria | quem fez o quê, quando, IP | segurança e prestação de contas (art. 37 e 46) | legítimo interesse (art. 7º, IX) | Neon (não pode ser alterado nem apagado) | 👤 proposta: 5 anos |
| Sessões de login | IP, navegador, horários | permitir "Sair" e cortar acessos | legítimo interesse | Neon | apagadas 30 dias depois de vencerem (automático) |
| Cópias de segurança | tudo acima | voltar ao ar depois de um problema | legítimo interesse / segurança (art. 46) | GitHub, **criptografado** com chave que só a casa tem | 30 dias (apagado automaticamente) |

## Dados sensíveis

Participar de atendimentos numa casa espírita revela **convicção religiosa**,
e as observações podem falar de **saúde** — os dois são dados sensíveis (art.
5º, II). Por isso:

- o consentimento é registrado na ficha, com data (`consentimento_lgpd` e
  `consentimento_em`); 👤 o ideal é a pessoa assinar o termo na ficha de papel
  e a equipe marcar no sistema;
- as observações, o diário e os anexos ficam cifrados no banco;
- só a equipe cadastrada acessa, com login individual e tudo registrado.

### Assistidos e menores 👤

O tratamento pode incluir pessoas que **não vieram à casa** (alguém pede por
filhos, pais, cônjuge). A casa precisa decidir e registrar como obtém o
consentimento delas (ou de quem responde por elas). Para **criança ou
adolescente**, a LGPD (art. 14) exige consentimento específico de pelo menos
um dos pais ou responsável legal.

## Minimização

Todos os campos do cadastro vêm da ficha de papel da casa e são usados. Só o
nome é obrigatório; CPF, endereço e o resto são opcionais. 👤 Se algum campo
deixar de ser usado, avise pra ele sair do formulário e do banco.

## Retenção 👤

Já é automático: sessões vencidas (30 dias) e cópias de segurança (30 dias).

**A casa precisa decidir:** por quanto tempo guardar a ficha de quem não vem
mais. Proposta: fichas sem atendimento há **5 anos** são anonimizadas (o
sistema já faz isso por ficha — botão "Anonimizar"; dá pra automatizar
depois que a regra for decidida).

Depois de uma anonimização, os dados ainda existem nas cópias de segurança
por até 30 dias, até elas expirarem. Se for preciso restaurar um backup
nesse período, a ficha anonimizada tem que ser anonimizada de novo.

## Direitos do titular (art. 18)

Canal: pessoalmente, com a coordenação da casa. 👤 Se houver e-mail ou
telefone oficial, inclua na política de privacidade. Prazo interno: **até 15
dias**.

| Pedido | Como atender no sistema |
|---|---|
| Saber se a casa tem dados e receber uma cópia | Ficha → LGPD → **Exportar dados (JSON)** (admin) |
| Corrigir | Ficha → **Editar** |
| Excluir / anonimizar | Ficha → LGPD → **Anonimizar** (admin) — apaga dados pessoais e arquivos, mantém só o registro sem identificação |
| Retirar o consentimento | Ficha → Editar → desmarcar o consentimento (e, se pedir, anonimizar) |
| Saber com quem os dados são compartilhados | Política de privacidade (`/privacidade`) |

## Encarregado (DPO) 👤

A Resolução CD/ANPD nº 2/2022 dispensa **agentes de tratamento de pequeno
porte** (inclusive entidades sem fins lucrativos) de indicar um encarregado,
desde que ofereçam um canal pro titular — mas a dispensa não vale pra quem
faz tratamento de **alto risco**. Tratar dado sensível conta pra isso, então
vale confirmar com advogado(a) se a casa se enquadra. Se não se enquadrar,
indicar uma pessoa e publicar o contato dela na política de privacidade.

## Terceiros que tocam nos dados

| Serviço | Papel | Onde | Termos |
|---|---|---|---|
| Neon | banco de dados | EUA (região escolhida no projeto) | termos de proteção de dados (DPA) no site do Neon |
| Render | servidor da API | EUA | DPA no site do Render |
| Vercel | site (só arquivos do site; os dados passam direto do navegador pra API) | global | DPA no site da Vercel |
| GitHub | código e cópias de segurança criptografadas (a chave fica com a casa) | EUA | DPA no site do GitHub |

Os dados podem ficar fora do Brasil (transferência internacional, art. 33).
Esses provedores oferecem cláusulas contratuais de proteção de dados. 👤
Vale a revisão jurídica confirmar se isso basta pra casa.

## Quem tem acesso

Só usuários cadastrados na tela **Usuários**. 👤 Revisar a lista a cada 3
meses e desativar no mesmo dia quem sair da equipe (ver
[SEGURANCA.md](SEGURANCA.md), "Rotina").
