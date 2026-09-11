import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export function Pessoas() {
  const { usuario, sair } = useAuth()

  const [busca, setBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    setCarregando(true)
    setErro('')

    const params = new URLSearchParams({ page: pagina, size: 20 })
    if (busca.trim()) params.set('q', busca.trim())

    // pequena espera pra não disparar uma busca a cada letra digitada
    const timer = setTimeout(() => {
      api
        .get(`/pessoas?${params}`)
        .then(setDados)
        .catch((e) => setErro(e.message))
        .finally(() => setCarregando(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [busca, pagina])

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">
        <h1 className="text-lg font-bold text-slate-800">Casa Espírita</h1>
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <span>
            {usuario.nome} <span className="text-slate-400">({usuario.papel})</span>
          </span>
          <button
            onClick={sair}
            className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-50"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-4xl p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-bold text-slate-800">Pessoas</h2>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Buscar por nome, telefone ou CPF..."
              value={busca}
              onChange={(e) => {
                setPagina(1)
                setBusca(e.target.value)
              }}
              className="w-64 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            />
            <Link
              to="/pessoas/nova"
              className="whitespace-nowrap rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              + Nova pessoa
            </Link>
          </div>
        </div>

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm">
          {erro && <p className="p-4 text-sm text-red-600">{erro}</p>}

          {!erro && carregando && (
            <p className="p-4 text-sm text-slate-500">Carregando...</p>
          )}

          {!erro && !carregando && dados?.items.length === 0 && (
            <p className="p-4 text-sm text-slate-500">Nenhuma pessoa encontrada.</p>
          )}

          {!erro && !carregando && dados?.items.length > 0 && (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Nome</th>
                  <th className="px-4 py-2 font-medium">Telefone</th>
                  <th className="px-4 py-2 font-medium">Cidade</th>
                  <th className="px-4 py-2 font-medium">Papel</th>
                </tr>
              </thead>
              <tbody>
                {dados.items.map((p) => (
                  <tr key={p.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-2">
                      <Link
                        to={`/pessoas/${p.id}`}
                        className="font-medium text-slate-800 hover:underline"
                      >
                        {p.nome_completo}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-slate-600">{p.telefone || '—'}</td>
                    <td className="px-4 py-2 text-slate-600">
                      {p.cidade ? `${p.cidade}${p.uf ? '/' + p.uf : ''}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-600">
                      {p.papeis.join(', ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {dados && dados.pages > 1 && (
          <div className="mt-4 flex items-center justify-center gap-3 text-sm text-slate-600">
            <button
              disabled={pagina <= 1}
              onClick={() => setPagina((p) => p - 1)}
              className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
            >
              Anterior
            </button>
            <span>
              Página {dados.page} de {dados.pages}
            </span>
            <button
              disabled={pagina >= dados.pages}
              onClick={() => setPagina((p) => p + 1)}
              className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
