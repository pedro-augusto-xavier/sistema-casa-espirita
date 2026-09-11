import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { Modal } from './Modal'

const ROTULO_STATUS_ASSISTIDO = {
  ativo: 'Em andamento',
  concluido: 'Concluído',
  removido: 'Removido',
}

export function TratamentoDetalheModal({ tratamentoId, onFechar }) {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [novaEvolucao, setNovaEvolucao] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    carregar()
  }, [tratamentoId])

  function carregar() {
    api
      .get(`/tratamentos/${tratamentoId}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }

  async function adicionarEvolucao(evento) {
    evento.preventDefault()
    if (!novaEvolucao.trim()) return
    setEnviando(true)
    setErro('')
    try {
      await api.post(`/tratamentos/${tratamentoId}/evolucoes`, {
        texto: novaEvolucao.trim(),
      })
      setNovaEvolucao('')
      carregar()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  async function concluirAssistido(assistidoId) {
    const situacao = prompt('Situação final (opcional):') ?? ''
    try {
      await api.patch(`/tratamentos/${tratamentoId}/assistidos/${assistidoId}`, {
        status: 'concluido',
        situacao_final: situacao || null,
        data_conclusao: new Date().toISOString().slice(0, 10),
      })
      carregar()
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <Modal titulo="Tratamento" onFechar={onFechar}>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="text-sm text-slate-500">Carregando...</p>}

      {dados && (
        <div className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto text-sm">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
            <Item label="Tipo" valor={dados.tipo_nome} />
            <Item label="Status" valor={dados.status === 'concluido' ? 'Concluído' : 'Em andamento'} />
            <Item label="Início" valor={isoParaData(dados.data_inicio)} />
            <Item label="Solicitante" valor={dados.solicitante?.nome_completo} />
            <Item label="Sessões previstas" valor={dados.sessoes_previstas} />
          </dl>

          {dados.observacao && (
            <div>
              <p className="text-xs font-medium text-slate-400">Observação</p>
              <p className="text-slate-700">{dados.observacao}</p>
            </div>
          )}

          {dados.situacao_final && (
            <div>
              <p className="text-xs font-medium text-slate-400">Situação final</p>
              <p className="text-slate-700">{dados.situacao_final}</p>
            </div>
          )}

          <div>
            <p className="mb-2 text-xs font-medium text-slate-400">Assistidos</p>
            <ul className="flex flex-col gap-1">
              {dados.assistidos.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center justify-between rounded-md bg-slate-50 px-2 py-1.5"
                >
                  <span
                    className={a.status !== 'ativo' ? 'text-slate-400 line-through' : 'text-slate-700'}
                  >
                    {a.pessoa.nome_completo}
                    <span className="ml-2 text-xs no-underline">
                      ({ROTULO_STATUS_ASSISTIDO[a.status]})
                    </span>
                  </span>
                  {a.status === 'ativo' && (
                    <button
                      onClick={() => concluirAssistido(a.id)}
                      className="text-xs text-slate-500 hover:text-slate-800 hover:underline"
                    >
                      Concluir
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="mb-2 text-xs font-medium text-slate-400">
              Diário de evolução
            </p>
            {dados.evolucoes.length === 0 ? (
              <p className="text-slate-500">Nenhuma anotação ainda.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {dados.evolucoes.map((e) => (
                  <li key={e.id} className="border-l-2 border-slate-300 pl-3">
                    <div className="flex items-baseline gap-2">
                      <span className="text-xs text-slate-400">{isoParaData(e.data)}</span>
                      {e.registrado_por && (
                        <span className="text-xs text-slate-400">
                          — {e.registrado_por.nome_completo}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-700">{e.texto}</p>
                  </li>
                ))}
              </ul>
            )}

            <form onSubmit={adicionarEvolucao} className="mt-3 flex gap-2">
              <input
                type="text"
                placeholder="Nova anotação..."
                value={novaEvolucao}
                onChange={(e) => setNovaEvolucao(e.target.value)}
                className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              />
              <button
                type="submit"
                disabled={enviando}
                className="rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
              >
                Adicionar
              </button>
            </form>
          </div>
        </div>
      )}
    </Modal>
  )
}

function Item({ label, valor }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-400">{label}</dt>
      <dd className="text-slate-700">{valor ?? '—'}</dd>
    </div>
  )
}
