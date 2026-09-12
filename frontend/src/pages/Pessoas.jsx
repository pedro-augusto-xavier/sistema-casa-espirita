import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { ResumoDoDia } from '../components/ResumoDoDia'
import { mascaraTelefone } from '../utils/formatadores'

export function Pessoas() {
  const [busca, setBusca] = useState('')
  const [papel, setPapel] = useState('')
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    setCarregando(true)
    setErro('')

    const params = new URLSearchParams({ page: pagina, size: 20 })
    if (busca.trim()) params.set('q', busca.trim())
    if (papel) params.set('papel', papel)
    if (incluirInativos) params.set('incluir_inativos', 'true')

    // pequena espera pra não disparar uma busca a cada letra digitada
    const timer = setTimeout(() => {
      api
        .get(`/pessoas?${params}`)
        .then(setDados)
        .catch((e) => setErro(e.message))
        .finally(() => setCarregando(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [busca, papel, incluirInativos, pagina])

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl p-6">
        <ResumoDoDia />

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-display text-2xl font-semibold text-emerald-900">Pessoas</h2>
          <Link
            to="/pessoas/nova"
            className="whitespace-nowrap rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 sm:hidden"
          >
            + Nova pessoa
          </Link>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            type="text"
            placeholder="Buscar por nome, telefone ou CPF..."
            value={busca}
            onChange={(e) => {
              setPagina(1)
              setBusca(e.target.value)
            }}
            className="w-64 rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
          />
          <select
            value={papel}
            onChange={(e) => {
              setPagina(1)
              setPapel(e.target.value)
            }}
            className="rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
          >
            <option value="">Todos os papéis</option>
            <option value="assistido">Assistido(a)</option>
            <option value="trabalhador">Trabalhador(a)</option>
          </select>
          <label className="flex items-center gap-1.5 text-sm text-stone-600">
            <input
              type="checkbox"
              checked={incluirInativos}
              onChange={(e) => {
                setPagina(1)
                setIncluirInativos(e.target.checked)
              }}
            />
            Mostrar inativos
          </label>
          <Link
            to="/pessoas/nova"
            className="ml-auto hidden whitespace-nowrap rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 sm:inline-block"
          >
            + Nova pessoa
          </Link>
        </div>

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-stone-900/5">
          {erro && <p className="p-4 text-sm text-red-600">{erro}</p>}

          {!erro && carregando && (
            <p className="p-4 text-sm text-stone-500">Carregando...</p>
          )}

          {!erro && !carregando && dados?.items.length === 0 && (
            <p className="p-4 text-sm text-stone-500">Nenhuma pessoa encontrada.</p>
          )}

          {!erro && !carregando && dados?.items.length > 0 && (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-stone-200 bg-stone-50 text-stone-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Nome</th>
                  <th className="px-4 py-2 font-medium">Telefone</th>
                  <th className="px-4 py-2 font-medium">Cidade</th>
                  <th className="px-4 py-2 font-medium">Papel</th>
                </tr>
              </thead>
              <tbody>
                {dados.items.map((p) => (
                  <tr key={p.id} className="border-b border-stone-100 last:border-0">
                    <td className="px-4 py-2">
                      <Link
                        to={`/pessoas/${p.id}`}
                        className="font-medium text-stone-800 hover:underline"
                      >
                        {p.nome_completo}
                      </Link>
                      {!p.ativo && (
                        <span className="ml-2 rounded-full bg-stone-200 px-2 py-0.5 text-xs text-stone-500">
                          inativa
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-stone-600">
                      {p.telefone ? mascaraTelefone(p.telefone) : '—'}
                    </td>
                    <td className="px-4 py-2 text-stone-600">
                      {p.cidade ? `${p.cidade}${p.uf ? '/' + p.uf : ''}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-stone-600">
                      {p.papeis.join(', ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {dados && dados.pages > 1 && (
          <div className="mt-4 flex items-center justify-center gap-3 text-sm text-stone-600">
            <button
              disabled={pagina <= 1}
              onClick={() => setPagina((p) => p - 1)}
              className="rounded-md border border-stone-300 px-3 py-1 disabled:opacity-40"
            >
              Anterior
            </button>
            <span>
              Página {dados.page} de {dados.pages}
            </span>
            <button
              disabled={pagina >= dados.pages}
              onClick={() => setPagina((p) => p + 1)}
              className="rounded-md border border-stone-300 px-3 py-1 disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
