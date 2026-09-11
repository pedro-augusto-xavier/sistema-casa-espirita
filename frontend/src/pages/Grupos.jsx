import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { GrupoModal } from '../components/GrupoModal'
import { isoParaData } from '../utils/formatadores'

export function Grupos() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [pagina, setPagina] = useState(1)
  const [modalAberto, setModalAberto] = useState(false)
  const [editando, setEditando] = useState(null)
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    api
      .get(`/grupos?page=${pagina}&size=20`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [pagina, versao])

  function aoSalvar() {
    setModalAberto(false)
    setEditando(null)
    setVersao((v) => v + 1)
  }

  async function excluir(id, evento) {
    evento.stopPropagation()
    if (!confirm('Excluir esta sessão de grupo?')) return
    try {
      await api.del(`/grupos/${id}`)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Cabecalho />

      <main className="mx-auto max-w-3xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800">Grupos</h2>
            <p className="text-sm text-slate-500">
              Grupo Despertar, Grupo de Estudos -- presença por sessão.
            </p>
          </div>
          <button
            onClick={() => setModalAberto(true)}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            + Nova sessão
          </button>
        </div>

        {erro && (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm">
          {!dados ? (
            <p className="p-4 text-sm text-slate-500">Carregando...</p>
          ) : dados.items.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">Nenhuma sessão registrada.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Data</th>
                  <th className="px-4 py-2 font-medium">Tipo</th>
                  <th className="px-4 py-2 font-medium">Responsável</th>
                  <th className="px-4 py-2 font-medium">Presentes</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {dados.items.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => setEditando(s.id)}
                    className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50"
                  >
                    <td className="px-4 py-2 text-slate-600">{isoParaData(s.data)}</td>
                    <td className="px-4 py-2 font-medium text-slate-800">{s.tipo_nome}</td>
                    <td className="px-4 py-2 text-slate-600">
                      {s.responsavel?.nome_completo || '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-600">{s.qtd_presentes}</td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={(e) => excluir(s.id, e)}
                        className="text-xs text-red-500 hover:underline"
                      >
                        Excluir
                      </button>
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

      {modalAberto && <GrupoModal onFechar={() => setModalAberto(false)} onSalvo={aoSalvar} />}
      {editando && (
        <DetalheGrupo id={editando} onFechar={() => setEditando(null)} onSalvo={aoSalvar} />
      )}
    </div>
  )
}

function DetalheGrupo({ id, onFechar, onSalvo }) {
  const [existente, setExistente] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/grupos/${id}`)
      .then(setExistente)
      .catch((e) => setErro(e.message))
  }, [id])

  if (erro) return <p className="p-6 text-sm text-red-600">{erro}</p>
  if (!existente) return null

  return <GrupoModal existente={existente} onFechar={onFechar} onSalvo={onSalvo} />
}
