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
import { mascaraCpf, nomeDeLogin, senhaDeCpf } from '../utils/formatadores'

const VAZIO = { nome: '', email: '', senha: '', papel: 'operador' }

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
  // só ajudam a preencher nome/senha -- não vão pro servidor
  const [ajudaNome, setAjudaNome] = useState('')
  const [ajudaCpf, setAjudaCpf] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [redefinindo, setRedefinindo] = useState(null) // usuário

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
      await api.post('/usuarios', { ...novo, email: novo.email || null })
      setNovo(VAZIO)
      setAjudaNome('')
      setAjudaCpf('')
      atualizar('Usuário criado. No primeiro acesso a pessoa vai criar a própria senha.')
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  function preencherComNomeECpf() {
    setNovo((n) => ({
      ...n,
      nome: nomeDeLogin(ajudaNome) || n.nome,
      senha: senhaDeCpf(ajudaCpf) || n.senha,
    }))
  }

  async function acao(promessa, mensagem) {
    try {
      await promessa
      atualizar(mensagem)
    } catch (e) {
      setErro(e.message)
    }
  }

  function alternarAtivo(u) {
    if (u.ativo && !confirm(`Desativar ${u.nome}? A pessoa é desconectada na hora.`)) return
    acao(
      api.patch(`/usuarios/${u.id}`, { ativo: !u.ativo }),
      u.ativo ? `${u.nome} foi desativado(a) e desconectado(a).` : `${u.nome} foi reativado(a).`,
    )
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
                — login = primeiro + último nome · senha provisória = 8 primeiros números do CPF
              </span>
            </p>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-[2fr_1fr_auto]">
              <input
                placeholder="Nome completo"
                value={ajudaNome}
                onChange={(e) => setAjudaNome(e.target.value)}
                className="campo border-transparent bg-white shadow-none"
              />
              <input
                placeholder="CPF"
                inputMode="numeric"
                maxLength={14}
                value={ajudaCpf}
                onChange={(e) => setAjudaCpf(mascaraCpf(e.target.value))}
                className="campo border-transparent bg-white shadow-none"
              />
              <Botao
                type="button"
                variante="secundario"
                onClick={preencherComNomeECpf}
                disabled={!ajudaNome.trim() && !ajudaCpf.trim()}
              >
                Preencher
              </Botao>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
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
            <Campo label="Senha provisória">
              <div className="flex items-center gap-2">
                <input
                  required
                  type={mostrarSenha ? 'text' : 'password'}
                  minLength={8}
                  placeholder="8+ caracteres"
                  autoComplete="new-password"
                  value={novo.senha}
                  onChange={(e) => setNovo((n) => ({ ...n, senha: e.target.value }))}
                  className="campo"
                />
                <button
                  type="button"
                  onClick={() => setMostrarSenha((v) => !v)}
                  className="shrink-0 text-xs text-stone-400 hover:text-emerald-800 hover:underline"
                >
                  {mostrarSenha ? 'ocultar' : 'ver'}
                </button>
              </div>
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
              No primeiro acesso a pessoa troca a senha provisória por uma só dela
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
          onSalvo={() => {
            const nome = redefinindo.nome
            setRedefinindo(null)
            atualizar(`Senha de ${nome} redefinida. Ela vale só pro próximo acesso.`)
          }}
        />
      )}
    </div>
  )
}

function RedefinirSenhaModal({ usuario, onFechar, onSalvo }) {
  const [senha, setSenha] = useState('')
  const [cpf, setCpf] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function salvar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await api.patch(`/usuarios/${usuario.id}`, { senha })
      onSalvo()
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
          A senha nova é provisória: serve só pro próximo acesso, quando a pessoa cria a dela. Quem
          estiver logado com essa conta é desconectado.
        </p>
        <div className="flex items-end gap-2">
          <CampoUi label="Preencher com o CPF" dica="opcional" className="flex-1">
            <input
              inputMode="numeric"
              maxLength={14}
              value={cpf}
              onChange={(e) => setCpf(mascaraCpf(e.target.value))}
              className="campo"
            />
          </CampoUi>
          <Botao
            variante="secundario"
            type="button"
            disabled={!senhaDeCpf(cpf)}
            onClick={() => setSenha(senhaDeCpf(cpf))}
          >
            Usar 8 números
          </Botao>
        </div>
        <CampoUi label="Senha provisória">
          <input
            required
            minLength={8}
            autoComplete="new-password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            className="campo font-mono"
          />
        </CampoUi>
        <MensagemErro>{erro}</MensagemErro>
        <div className="flex justify-end gap-2">
          <Botao variante="secundario" type="button" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : 'Redefinir'}
          </Botao>
        </div>
      </form>
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
