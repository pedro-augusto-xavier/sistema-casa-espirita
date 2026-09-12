import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { useAuth } from '../auth/AuthContext'
import {
  Avatar,
  Botao,
  Carregando,
  MensagemErro,
  Pill,
  TituloPagina,
} from '../components/ui'

const VAZIO = { nome: '', email: '', senha: '', papel: 'operador' }

export function Usuarios() {
  const { usuario: eu } = useAuth()
  const [lista, setLista] = useState(null)
  const [erro, setErro] = useState('')
  const [novo, setNovo] = useState(VAZIO)
  const [enviando, setEnviando] = useState(false)
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    api
      .get('/usuarios')
      .then((d) => setLista(d.items))
      .catch((e) => setErro(e.message))
  }, [versao])

  async function criar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await api.post('/usuarios', novo)
      setNovo(VAZIO)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  async function alternarAtivo(usuario) {
    try {
      await api.patch(`/usuarios/${usuario.id}`, { ativo: !usuario.ativo })
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <TituloPagina
          titulo="Usuários do sistema"
          subtitulo="Quem pode entrar no sistema e fazer os cadastros."
        />

        <form
          onSubmit={criar}
          className="mt-5 rounded-xl bg-white p-5 shadow-sm ring-1 ring-stone-900/5"
        >
          <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
            Novo usuário
          </p>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Campo label="Nome">
              <input
                required
                value={novo.nome}
                onChange={(e) => setNovo((n) => ({ ...n, nome: e.target.value }))}
                className="campo"
              />
            </Campo>
            <Campo label="E-mail">
              <input
                required
                type="email"
                value={novo.email}
                onChange={(e) => setNovo((n) => ({ ...n, email: e.target.value }))}
                className="campo"
              />
            </Campo>
            <Campo label="Senha">
              <input
                required
                type="password"
                minLength={8}
                placeholder="8+ caracteres"
                value={novo.senha}
                onChange={(e) => setNovo((n) => ({ ...n, senha: e.target.value }))}
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
          <div className="mt-4 flex justify-end">
            <Botao type="submit" disabled={enviando}>
              {enviando ? 'Criando...' : '+ Criar usuário'}
            </Botao>
          </div>
        </form>

        <MensagemErro className="mt-4">{erro}</MensagemErro>

        <div className="mt-5 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!lista ? (
            <Carregando />
          ) : (
            <ul className="divide-y divide-stone-100">
              {lista.map((u) => (
                <li
                  key={u.id}
                  className={`flex items-center gap-4 px-4 py-3 sm:px-5 ${u.ativo ? '' : 'opacity-60'}`}
                >
                  <Avatar nome={u.nome} />
                  <div className="min-w-0 flex-1">
                    <p className="flex flex-wrap items-center gap-2 font-medium text-stone-800">
                      <span className="truncate">{u.nome}</span>
                      {u.id === eu.id && (
                        <span className="text-xs font-normal text-stone-400">(você)</span>
                      )}
                    </p>
                    <p className="truncate text-xs text-stone-500">{u.email}</p>
                  </div>
                  <div className="hidden shrink-0 items-center gap-1.5 sm:flex">
                    <Pill tom={u.papel === 'admin' ? 'ambar' : 'cinza'}>
                      {u.papel === 'admin' ? 'Admin' : 'Operador'}
                    </Pill>
                    <Pill tom={u.ativo ? 'verde' : 'cinza'}>{u.ativo ? 'Ativo' : 'Inativo'}</Pill>
                  </div>
                  {u.id !== eu.id && (
                    <Botao variante="fantasma" pequeno onClick={() => alternarAtivo(u)}>
                      {u.ativo ? 'Desativar' : 'Reativar'}
                    </Botao>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  )
}

function Campo({ label, children }) {
  return (
    <label className="block text-xs font-medium text-stone-600">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
