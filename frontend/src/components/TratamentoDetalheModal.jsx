import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { Modal } from './Modal'

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

  async function fecharCaso() {
    if (!confirm('Fechar este tratamento como concluído?')) return
    const situacao = prompt('Situação final do caso (opcional):') ?? ''
    try {
      await api.patch(`/tratamentos/${tratamentoId}`, {
        status: 'concluido',
        situacao_final: situacao || null,
      })
      carregar()
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <Modal titulo="" onFechar={onFechar}>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="text-sm text-slate-500">Carregando...</p>}

      {dados && (
        <div className="flex max-h-[75vh] flex-col gap-5 overflow-y-auto text-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold uppercase tracking-wide text-slate-800">
                {dados.tipo_nome}
              </h2>
              <span
                className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  dados.status === 'concluido'
                    ? 'bg-slate-200 text-slate-600'
                    : 'bg-emerald-100 text-emerald-700'
                }`}
              >
                {dados.status === 'concluido' ? 'Concluído' : 'Em andamento'}
              </span>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                onClick={async () => {
                  const { gerarPdfTratamento } = await import(
                    '../utils/gerarPdfTratamento'
                  )
                  gerarPdfTratamento(dados)
                }}
                className="rounded-md border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
              >
                Baixar PDF
              </button>
              {dados.status !== 'concluido' && (
                <button
                  onClick={fecharCaso}
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
                >
                  Fechar caso
                </button>
              )}
            </div>
          </div>

          <Secao titulo="Responsável">
            <p className="text-slate-700">{dados.solicitante?.nome_completo || '—'}</p>
          </Secao>

          <Secao titulo="Assistidos">
            <ul className="flex flex-col gap-1">
              {dados.assistidos.map((a) => (
                <li key={a.id} className="flex items-center justify-between">
                  <span
                    className={
                      a.status !== 'ativo'
                        ? 'text-slate-400 line-through decoration-2'
                        : 'text-slate-700'
                    }
                  >
                    {a.pessoa.nome_completo}
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
          </Secao>

          <div className="grid grid-cols-2 gap-4 border-y border-slate-200 py-3">
            <Campo label="Início" valor={isoParaData(dados.data_inicio)} />
            <Campo label="Sessões previstas" valor={dados.sessoes_previstas} />
          </div>

          {dados.observacao && <Secao titulo="Observação">{dados.observacao}</Secao>}
          {dados.situacao_final && (
            <Secao titulo="Situação final">{dados.situacao_final}</Secao>
          )}

          <Secao titulo="Diário de evolução">
            {dados.evolucoes.length === 0 ? (
              <p className="text-slate-500">Nenhuma anotação ainda.</p>
            ) : (
              <div className="flex flex-col gap-3">
                {dados.evolucoes.map((e) => (
                  <p key={e.id} className="leading-relaxed text-slate-700">
                    <span className="font-bold">{isoParaData(e.data)}</span>
                    {e.registrado_por && (
                      <span className="text-slate-400"> — {e.registrado_por.nome_completo}</span>
                    )}
                    {' — '}
                    {e.texto}
                  </p>
                ))}
              </div>
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
          </Secao>
        </div>
      )}
    </Modal>
  )
}

function Secao({ titulo, children }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-slate-400">
        {titulo}
      </h3>
      {children}
    </div>
  )
}

function Campo({ label, valor }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-slate-700">{valor ?? '—'}</p>
    </div>
  )
}
