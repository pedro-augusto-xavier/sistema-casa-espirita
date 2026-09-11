import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { AgendaModal } from '../components/AgendaModal'
import { Cabecalho } from '../components/Cabecalho'

const ROTULO_TIPO = {
  trabalho: 'Trabalho',
  palestra: 'Palestra',
  grupo: 'Grupo',
  outro: 'Outro',
}

function formatarDataHora(iso) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function Agenda() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [tipo, setTipo] = useState('')
  const [pagina, setPagina] = useState(1)
  const [modalAberto, setModalAberto] = useState(false)
  const [editando, setEditando] = useState(null)
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    const params = new URLSearchParams({ page: pagina, size: 20 })
    if (tipo) params.set('tipo', tipo)
    api
      .get(`/agenda?${params}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [tipo, pagina, versao])

  function aoSalvar() {
    setModalAberto(false)
    setEditando(null)
    setVersao((v) => v + 1)
  }

  async function excluir(id, evento) {
    evento.stopPropagation()
    if (!confirm('Excluir este evento da agenda?')) return
    try {
      await api.del(`/agenda/${id}`)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Cabecalho />

      <main className="mx-auto max-w-3xl p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-bold text-slate-800">Agenda</h2>
          <button
            onClick={() => setModalAberto(true)}
            className="whitespace-nowrap rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            + Novo evento
          </button>
        </div>

        <div className="mt-3">
          <select
            value={tipo}
            onChange={(e) => {
              setPagina(1)
              setTipo(e.target.value)
            }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
          >
            <option value="">Todos os tipos</option>
            {Object.entries(ROTULO_TIPO).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>

        {erro && (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm">
          {!dados ? (
            <p className="p-4 text-sm text-slate-500">Carregando...</p>
          ) : dados.items.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">Nada na agenda.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Quando</th>
                  <th className="px-4 py-2 font-medium">Título</th>
                  <th className="px-4 py-2 font-medium">Tipo</th>
                  <th className="px-4 py-2 font-medium">Escalados</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {dados.items.map((ev) => (
                  <tr
                    key={ev.id}
                    onClick={() => setEditando(ev.id)}
                    className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50"
                  >
                    <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                      {formatarDataHora(ev.data_inicio)}
                    </td>
                    <td className="px-4 py-2 font-medium text-slate-800">{ev.titulo}</td>
                    <td className="px-4 py-2 text-slate-600">{ROTULO_TIPO[ev.tipo]}</td>
                    <td className="px-4 py-2 text-slate-600">{ev.qtd_escalados}</td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={(e) => excluir(ev.id, e)}
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

      {modalAberto && <AgendaModal onFechar={() => setModalAberto(false)} onSalvo={aoSalvar} />}
      {editando && (
        <DetalheEvento id={editando} onFechar={() => setEditando(null)} onSalvo={aoSalvar} />
      )}
    </div>
  )
}

function DetalheEvento({ id, onFechar, onSalvo }) {
  const [existente, setExistente] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/agenda/${id}`)
      .then(setExistente)
      .catch((e) => setErro(e.message))
  }, [id])

  if (erro) return <p className="p-6 text-sm text-red-600">{erro}</p>
  if (!existente) return null

  return <AgendaModal existente={existente} onFechar={onFechar} onSalvo={onSalvo} />
}
