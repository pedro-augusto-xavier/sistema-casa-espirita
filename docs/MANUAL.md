# Manual do voluntário

Como usar o sistema no dia a dia da casa. Os nomes entre aspas são os
botões e campos exatamente como aparecem na tela.

## Entrar

1. Abra o endereço do sistema no navegador (celular ou computador).
2. Em **Nome**, digite seu nome do jeito que foi cadastrado. O login é pelo
   nome, não pelo e-mail.
3. Digite a **Senha** e toque em **Entrar**.

Se o sistema ficou um tempo sem ninguém usar, o primeiro acesso pode
demorar **até 1 minuto**. Espere: não é erro.

**"Manter conectado neste aparelho"**: deixe marcado só no seu aparelho.
Num computador da casa usado por várias pessoas, desmarque e use **Sair**
no fim.

### Primeiro acesso

Quem cuida do sistema cria seu usuário e te passa uma **senha provisória**.
Ela vale 72 horas e só serve uma vez. No primeiro acesso o sistema pede:

1. **Criar a sua senha.** Escolha uma que só você saiba.
2. **"Mais uma proteção"**, a verificação em duas etapas. Instale no celular
   um aplicativo autenticador (Google Authenticator, Microsoft
   Authenticator…), leia o QR code da tela e digite o código de 6 números.
   Para administradores é obrigatória; para os demais, é recomendada.

Com a verificação ligada, todo login pede também o código do aplicativo.

## Achar uma pessoa

A tela inicial é **Pessoas**. Na busca, digite o nome, o telefone ou o CPF
completo. Dá para filtrar por papel (assistido, trabalhador, voluntário).

Antes de cadastrar alguém, **procure primeiro** para não criar uma ficha
repetida.

## Cadastrar uma ficha

1. Toque em **+ Nova pessoa**.
2. Preencha pelo menos **Nome completo**, **Data de nascimento**
   (dd/mm/aaaa) e **Sexo**. O resto é opcional.
3. Toque em **Salvar ficha**.

Para corrigir depois, abra a ficha e toque em **Editar**.

## Registrar um atendimento

1. Abra a ficha da pessoa e toque em **+ Registrar atendimento**.
2. Confira a **Data** (vem preenchida com hoje) e a **Modalidade**
   (presencial, vídeo ou à distância).
3. Em **Atendido por**, escolha quem atendeu.
4. Se a pessoa não veio, desmarque **"A pessoa esteve presente"** e diga
   quem veio no lugar dela.
5. Em **Tratamentos do dia**, toque nos tratamentos passados (ficam com ✓).
6. Escreva na **Observação** o que foi conversado e as orientações.
7. Toque em **Registrar**.

### Tratamentos com acompanhamento (casos)

Alguns tratamentos, como a Desobsessão, abrem uma **ficha de acompanhamento**
própria. Ao marcar um deles no atendimento, aparece um quadro amarelo onde
você informa:

- **Nº de vezes** previstas.
- **Assistidos**: por quem a pessoa pediu (ela mesma, filhos, amigos…). Use
  "Adicionar assistido" para buscar ou cadastrar.

Se a pessoa já tem esse tratamento aberto, o atendimento conta como mais
uma vez no mesmo caso.

Na ficha da pessoa, abra o tratamento para:

- escrever no **Diário** (ex.: "limpeza + doação + 3 choques");
- marcar um assistido como **Concluído**, com a situação final;
- **Reativar** quem foi concluído por engano.

## O histórico da pessoa

Na ficha aparece o **Histórico**: atendimentos, inícios de tratamento e
evolução, do mais recente para o mais antigo. Use **"Buscar no
histórico..."** para achar uma anotação. Toque num item para ver os
detalhes ou corrigir.

O CPF aparece escondido. O botão para mostrar o CPF completo fica registrado
na auditoria: só use quando precisar.

## Arquivos

Em **Arquivos**, na ficha, toque em **+ Adicionar** para guardar foto de
documento, receita etc. (até 8 MB). Os arquivos ficam criptografados.

## Agenda

Em **Agenda** ficam os trabalhos, palestras e reuniões de grupo, com a
escala de quem participa. Toque em **+ Novo evento**, preencha **Título**,
**Tipo**, **Início** e, se repetir, a **Recorrência**. Adicione as pessoas
da escala com a função de cada uma.

## Minha conta

No topo, **Minha conta** permite:

- **Trocar minha senha.** Os outros aparelhos são desconectados.
- Ligar ou desligar a **Verificação em duas etapas** (para admin, não dá
  para desligar).

## Problemas comuns

| Aconteceu | O que fazer |
|---|---|
| Esqueci a senha | Peça a um administrador para **gerar uma senha nova** (provisória). |
| Perdi ou troquei o celular do código | Peça a um administrador para **zerar a verificação em duas etapas**; no próximo acesso você configura de novo. |
| "Algo deu errado nesta tela" | Toque em **Recarregar**. O que já estava salvo não se perde. Se repetir, avise quem cuida do sistema dizendo o que estava fazendo. |
| Sistema muito lento ao abrir | Espere até 1 minuto (ver "Entrar"). |
| Cadastrei uma pessoa repetida | Avise um administrador; não apague dados por conta própria. |

## Para administradores

### Usuários

Em **Usuários**:

- **+ Criar usuário**: informe o **Nome** (é o login), o **Papel** (admin
  ou operador) e, se quiser, o e-mail. O sistema gera a senha provisória e
  mostra **uma vez só**. Copie e passe para a pessoa pessoalmente ou por
  mensagem direta.
- **Gerar senha nova**: para quem esqueceu a senha.
- **Zerar a verificação em duas etapas**: para quem perdeu o celular.
- **Desativar**: quando alguém sai da equipe. A pessoa é desconectada na
  hora.

### Auditoria

Em **Auditoria** fica quem entrou, criou, alterou, viu ou exportou cada
coisa, com data, hora e IP. Se aparecer **"Atenção: tem movimento fora do
comum"**, confira os itens destacados (ex.: muitos logins que falharam).

### Pedidos de LGPD

Na ficha da pessoa:

- **Exportar dados (JSON)**: quando a pessoa pede uma cópia dos dados dela.
- **Anonimizar**: quando a pessoa pede para apagar os dados pessoais. Apaga
  CPF, telefone, endereço etc. e **não pode ser desfeito**; o histórico de
  atendimentos é mantido.

Detalhes em [LGPD.md](LGPD.md).
