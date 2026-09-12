import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'

const VAZIO = { nome: '', email: '', senha: '', papel: 'operador' }

export function Usuarios() {
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

      <main className="mx-auto max-w-3xl p-6">
        <h2 className="font-display text-2xl font-semibold text-emerald-900">
          Usuários do sistema
        </h2>
        <p className="text-sm text-stone-500">
          Quem pode entrar no sistema e fazer os cadastros.
        </p>

        <form
          onSubmit={criar}
          className="mt-4 flex flex-wrap items-end gap-3 rounded-lg bg-white p-4 shadow-sm ring-1 ring-stone-900/5"
        >
          <Campo label="Nome">
            <input
              required
              value={novo.nome}
              onChange={(e) => setNovo((n) => ({ ...n, nome: e.target.value }))}
              className={estiloInput}
            />
          </Campo>
          <Campo label="E-mail">
            <input
              required
              type="email"
              value={novo.email}
              onChange={(e) => setNovo((n) => ({ ...n, email: e.target.value }))}
              className={estiloInput}
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
              className={estiloInput}
            />
          </Campo>
          <Campo label="Papel">
            <select
              value={novo.papel}
              onChange={(e) => setNovo((n) => ({ ...n, papel: e.target.value }))}
              className={estiloInput}
            >
              <option value="operador">Operador</option>
              <option value="admin">Admin</option>
            </select>
          </Campo>
          <button
            type="submit"
            disabled={enviando}
            className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {enviando ? 'Criando...' : '+ Criar usuário'}
          </button>
        </form>

        {erro && (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-stone-900/5">
          {!lista ? (
            <p className="p-4 text-sm text-stone-500">Carregando...</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-stone-200 bg-stone-50 text-stone-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Nome</th>
                  <th className="px-4 py-2 font-medium">E-mail</th>
                  <th className="px-4 py-2 font-medium">Papel</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {lista.map((u) => (
                  <tr key={u.id} className="border-b border-stone-100 last:border-0">
                    <td className="px-4 py-2">{u.nome}</td>
                    <td className="px-4 py-2 text-stone-600">{u.email}</td>
                    <td className="px-4 py-2 text-stone-600">{u.papel}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          u.ativo
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-stone-200 text-stone-500'
                        }`}
                      >
                        {u.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => alternarAtivo(u)}
                        className="text-xs text-stone-500 hover:underline"
                      >
                        {u.ativo ? 'Desativar' : 'Reativar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  )
}

const estiloInput =
  'w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15'

function Campo({ label, children }) {
  return (
    <label className="block text-xs font-medium text-stone-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
