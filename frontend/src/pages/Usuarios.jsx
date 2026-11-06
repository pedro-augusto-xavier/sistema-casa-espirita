import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { Modal } from '../components/Modal'
import { useAuth } from '../auth/AuthContext'
import {
  Avatar,
  Botao,
  Campo as CampoUi,
  Carregando,
  MensagemErro,
  Pill,
  TituloPagina,
} from '../components/ui'
import { nomeDeLogin } from '../utils/formatadores'

const VAZIO = { nome: '', email: '', papel: 'operador' }

function quandoFoi(iso) {
  if (!iso) return 'nunca entrou'
  const data = new Date(iso)
  return `último acesso ${data.toLocaleDateString('pt-BR')} ${data.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

export function Usuarios() {
  const { usuario: eu } = useAuth()
  const [lista, setLista] = useState(null)
  const [erro, setErro] = useState('')
  const [aviso, setAviso] = useState('')
  const [novo, setNovo] = useState(VAZIO)
  const [enviando, setEnviando] = useState(false)
  const [versao, setVersao] = useState(0)
  // só ajuda a preencher o login -- não vai pro servidor
  const [ajudaNome, setAjudaNome] = useState('')
  const [redefinindo, setRedefinindo] = useState(null) // usuário
  // senha provisória que o servidor acabou de gerar -- mostrada uma vez só
  const [senhaGerada, setSenhaGerada] = useState(null)

  useEffect(() => {
    api
      .get('/usuarios')
      .then((d) => setLista(d.items))
      .catch((e) => setErro(e.message))
  }, [versao])

  function atualizar(mensagem = '') {
    setAviso(mensagem)
    setErro('')
    setVersao((v) => v + 1)
  }

  async function criar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const criado = await api.post('/usuarios', { ...novo, email: novo.email || null })
      setNovo(VAZIO)
      setAjudaNome('')
      setSenhaGerada(criado)
      atualizar('Usuário criado. No primeiro acesso a pessoa vai criar a própria senha.')
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  function preencherLogin() {
    setNovo((n) => ({ ...n, nome: nomeDeLogin(ajudaNome) || n.nome }))
  }

  async function acao(promessa, mensagem) {
    try {
      await promessa
      atualizar(mensagem)
    } catch (e) {
      setErro(e.message)
    }
  }

  async function alternarAtivo(u) {
    if (u.ativo) {
      if (!confirm(`Desativar ${u.nome}? A pessoa é desconectada na hora.`)) return
      acao(
        api.patch(`/usuarios/${u.id}`, { ativo: false }),
        `${u.nome} foi desativado(a) e desconectado(a).`,
      )
      return
    }
    if (
      !confirm(
        `Reativar ${u.nome}? A senha antiga deixa de valer: o sistema gera uma senha provisória nova (vale 72h).`,
      )
    )
      return
    try {
      setSenhaGerada(await api.post(`/usuarios/${u.id}/reativar`))
      atualizar(`${u.nome} foi reativado(a). No próximo acesso a pessoa cria a própria senha.`)
    } catch (e) {
      setErro(e.message)
    }
  }

  function zerarDuasEtapas(u) {
    if (
      !confirm(
        `Zerar a verificação em duas etapas de ${u.nome}? Use quando a pessoa perdeu ou trocou de celular.`,
      )
    )
      return
    acao(
      api.post(`/usuarios/${u.id}/resetar-mfa`),
      `Pronto. ${u.nome} configura o código de novo no próximo acesso.`,
    )
  }

  function desconectar(u) {
    if (!confirm(`Desconectar ${u.nome} de todos os aparelhos?`)) return
    acao(api.post(`/usuarios/${u.id}/encerrar-sessoes`), `${u.nome} foi desconectado(a).`)
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <TituloPagina
          titulo="Usuários do sistema"
          subtitulo="Quem pode entrar no sistema e fazer os cadastros. Login é pelo nome."
        />

        <form
          onSubmit={criar}
          className="mt-5 rounded-xl bg-white p-5 shadow-sm ring-1 ring-stone-900/5"
        >
          <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
            Novo usuário
          </p>

          {/* ---------- preenchimento automático (opcional) ---------- */}
          <div className="mt-3 rounded-lg bg-stone-50 p-3 ring-1 ring-stone-900/5">
            <p className="text-xs font-medium text-stone-600">
              Preencher automático
              <span className="ml-1.5 font-normal text-stone-400">
                — login = primeiro + último nome
              </span>
            </p>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-[1fr_auto]">
              <input
                placeholder="Nome completo"
                value={ajudaNome}
                onChange={(e) => setAjudaNome(e.target.value)}
                className="campo border-transparent bg-white shadow-none"
              />
              <Botao
                type="button"
                variante="secundario"
                onClick={preencherLogin}
                disabled={!ajudaNome.trim()}
              >
                Preencher
              </Botao>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Campo label="Nome" dica="é o login">
              <input
                required
                value={novo.nome}
                onChange={(e) => setNovo((n) => ({ ...n, nome: e.target.value }))}
                className="campo"
              />
            </Campo>
            <Campo label="E-mail" dica="opcional">
              <input
                type="email"
                value={novo.email}
                onChange={(e) => setNovo((n) => ({ ...n, email: e.target.value }))}
                className="campo"
              />
            </Campo>
            <Campo label="Papel">
              <select
                value={novo.papel}
                onChange={(e) => setNovo((n) => ({ ...n, papel: e.target.value }))}
                className="campo"
              >
                <option value="operador">Operador</option>
                <option value="admin">Admin</option>
              </select>
            </Campo>
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-stone-500">
              O sistema gera uma senha provisória (vale 72h). No primeiro acesso a pessoa troca por
              uma só dela
              {novo.papel === 'admin' && ' e configura o código do celular (obrigatório pra admin)'}.
            </p>
            <Botao type="submit" disabled={enviando}>
              {enviando ? 'Criando...' : '+ Criar usuário'}
            </Botao>
          </div>
        </form>

        <MensagemErro className="mt-4">{erro}</MensagemErro>
        {aviso && (
          <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800 ring-1 ring-emerald-800/10">
            {aviso}
          </p>
        )}

        <div className="mt-5 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!lista ? (
            <Carregando />
          ) : (
            <ul className="divide-y divide-stone-100">
              {lista.map((u) => (
                <li
                  key={u.id}
                  className={`flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-5 ${u.ativo ? '' : 'opacity-60'}`}
                >
                  <Avatar nome={u.nome} />
                  <div className="min-w-0 flex-1">
                    <p className="flex flex-wrap items-center gap-2 font-medium text-stone-800">
                      <span className="truncate">{u.nome}</span>
                      {u.id === eu.id && (
                        <span className="text-xs font-normal text-stone-400">(você)</span>
                      )}
                    </p>
                    <p className="truncate text-xs text-stone-500">
                      {u.email || <span className="text-stone-300">sem e-mail</span>}
                      <span className="text-stone-300"> · </span>
                      {quandoFoi(u.ultimo_login_em)}
                    </p>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      <Pill tom={u.papel === 'admin' ? 'ambar' : 'cinza'}>
                        {u.papel === 'admin' ? 'Admin' : 'Operador'}
                      </Pill>
                      <Pill tom={u.ativo ? 'verde' : 'cinza'}>{u.ativo ? 'Ativo' : 'Inativo'}</Pill>
                      {u.senha_provisoria && <Pill tom="ambar">senha provisória</Pill>}
                      {u.mfa_ativo ? (
                        <Pill tom="verde">2 etapas ✓</Pill>
                      ) : (
                        u.mfa_obrigatorio && <Pill tom="vermelho">2 etapas pendente</Pill>
                      )}
                    </div>
                  </div>
                  {u.id !== eu.id && (
                    <div className="flex flex-wrap gap-1">
                      {u.ativo && (
                        <>
                          <Botao variante="fantasma" pequeno onClick={() => setRedefinindo(u)}>
                            Redefinir senha
                          </Botao>
                          {u.mfa_ativo && (
                            <Botao variante="fantasma" pequeno onClick={() => zerarDuasEtapas(u)}>
                              Zerar 2 etapas
                            </Botao>
                          )}
                          <Botao variante="fantasma" pequeno onClick={() => desconectar(u)}>
                            Desconectar
                          </Botao>
                        </>
                      )}
                      <Botao variante="fantasma" pequeno onClick={() => alternarAtivo(u)}>
                        {u.ativo ? 'Desativar' : 'Reativar'}
                      </Botao>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <p className="mt-4 text-xs text-stone-500">
          Alguém saiu da equipe? Desative no mesmo dia: a pessoa é desconectada na hora. Revise
          esta lista de tempos em tempos.
        </p>
      </main>

      {redefinindo && (
        <RedefinirSenhaModal
          usuario={redefinindo}
          onFechar={() => setRedefinindo(null)}
          onSalvo={(resposta) => {
            const nome = redefinindo.nome
            setRedefinindo(null)
            setSenhaGerada(resposta)
            atualizar(`Senha de ${nome} redefinida. Ela vale só pro próximo acesso.`)
          }}
        />
      )}

      {senhaGerada && (
        <SenhaGeradaModal dados={senhaGerada} onFechar={() => setSenhaGerada(null)} />
      )}
    </div>
  )
}

function RedefinirSenhaModal({ usuario, onFechar, onSalvo }) {
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function salvar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      onSalvo(await api.post(`/usuarios/${usuario.id}/redefinir-senha`))
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={`Redefinir senha de ${usuario.nome}`} onFechar={onFechar}>
      <form onSubmit={salvar} className="flex flex-col gap-4 text-sm">
        <p className="text-stone-600">
          O sistema gera uma senha provisória nova, que vale 72h e serve só pro próximo acesso,
          quando a pessoa cria a dela. Quem estiver logado com essa conta é desconectado.
        </p>
        <MensagemErro>{erro}</MensagemErro>
        <div className="flex justify-end gap-2">
          <Botao variante="secundario" type="button" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Gerando...' : 'Gerar senha nova'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}

function SenhaGeradaModal({ dados, onFechar }) {
  const [copiada, setCopiada] = useState(false)
  const expira = new Date(dados.senha_expira_em)

  async function copiar() {
    try {
      await navigator.clipboard.writeText(dados.senha_gerada)
      setCopiada(true)
    } catch {
      setCopiada(false)
    }
  }

  return (
    <Modal titulo={`Senha provisória de ${dados.nome}`} onFechar={onFechar}>
      <div className="flex flex-col gap-4 text-sm">
        <p className="text-stone-600">
          Passe esta senha pra pessoa. <strong>Ela não aparece de novo</strong> depois que você
          fechar esta janela.
        </p>
        <CampoUi label="Senha provisória">
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={dados.senha_gerada}
              onFocus={(e) => e.target.select()}
              className="campo font-mono"
            />
            <Botao variante="secundario" type="button" onClick={copiar}>
              {copiada ? 'Copiada ✓' : 'Copiar'}
            </Botao>
          </div>
        </CampoUi>
        <p className="text-xs text-stone-500">
          Vale até {expira.toLocaleDateString('pt-BR')}{' '}
          {expira.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}. Depois
          disso, só redefinindo de novo.
        </p>
        <div className="flex justify-end">
          <Botao type="button" onClick={onFechar}>
            Já anotei
          </Botao>
        </div>
      </div>
    </Modal>
  )
}

function Campo({ label, dica, children }) {
  return (
    <label className="block text-xs font-medium text-stone-600">
      {label}
      {dica && <span className="ml-1 font-normal text-stone-400">({dica})</span>}
      <div className="mt-1">{children}</div>
    </label>
  )
}
