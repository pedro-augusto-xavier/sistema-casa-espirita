import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { ROTULO_VINCULO, isoParaData } from '../utils/formatadores'
import { Modal } from './Modal'
import { Avatar, Botao, Carregando, MensagemErro, Pill, Rotulo } from './ui'

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

  async function excluir() {
    if (!confirm('Excluir este tratamento (caso, assistidos e diário)? Não pode ser desfeito.'))
      return
    try {
      await api.del(`/tratamentos/${tratamentoId}`)
      onFechar()
    } catch (e) {
      setErro(e.message)
    }
  }

  const concluido = dados?.status === 'concluido'

  return (
    <Modal titulo="" onFechar={onFechar} largura="max-w-xl">
      <MensagemErro>{erro}</MensagemErro>
      {!dados && !erro && <Carregando />}

      {dados && (
        <div className="flex flex-col gap-5 text-sm">
          <div className="border-b-2 border-emerald-900/80 pb-4">
            <Rotulo>Tratamento</Rotulo>
            <p className="mt-1 font-display text-3xl font-semibold text-emerald-950">
              {dados.tipo_nome}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <Pill tom={concluido ? 'cinza' : 'verde'}>
                {concluido ? 'Concluído' : 'Em andamento'}
              </Pill>
              <span className="text-xs text-stone-500">
                desde {isoParaData(dados.data_inicio)} · {dados.sessoes_realizadas ?? 0}
                {dados.sessoes_previstas ? ` de ${dados.sessoes_previstas}` : ''}{' '}
                {dados.sessoes_realizadas === 1 ? 'vez feita' : 'vezes feitas'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Rotulo>Responsável</Rotulo>
              <p className="text-xs text-stone-400">quem vem à casa</p>
              <p className="mt-1 text-stone-800">
                {dados.solicitante?.nome_completo || <span className="text-stone-300">—</span>}
              </p>
            </div>
            <div>
              <Rotulo>Assistidos</Rotulo>
              <p className="text-xs text-stone-400">por quem pediu</p>
              <ul className="mt-1 flex flex-col gap-1">
                {dados.assistidos.map((a) => (
                  <li key={a.id} className="flex items-center gap-2">
                    <Avatar nome={a.pessoa.nome_completo} className="h-6 w-6 text-[9px]" />
                    <span
                      className={`min-w-0 flex-1 truncate ${
                        a.status !== 'ativo' ? 'text-stone-400 line-through' : 'text-stone-800'
                      }`}
                    >
                      {a.pessoa.nome_completo}
                    </span>
                    {a.vinculo_com_responsavel && a.pessoa.id !== dados.solicitante?.id && (
                      <Pill tom="cinza" className="shrink-0 text-[10px]">
                        {ROTULO_VINCULO[a.vinculo_com_responsavel]}
                      </Pill>
                    )}
                    {a.status === 'ativo' && !concluido && (
                      <button
                        type="button"
                        onClick={() => concluirAssistido(a.id)}
                        className="text-xs text-stone-400 hover:text-emerald-800 hover:underline"
                      >
                        concluir
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {dados.observacao && (
            <div>
              <Rotulo className="mb-1.5">Observação</Rotulo>
              <p className="rounded-xl border-l-4 border-amber-400 bg-amber-50/60 p-3 leading-relaxed whitespace-pre-line text-stone-700">
                {dados.observacao}
              </p>
            </div>
          )}
          {dados.situacao_final && (
            <div>
              <Rotulo className="mb-1.5">Situação final</Rotulo>
              <p className="rounded-xl bg-stone-50 p-3 leading-relaxed text-stone-700 ring-1 ring-stone-900/5">
                {dados.situacao_final}
              </p>
            </div>
          )}

          {/* ---------- diário ---------- */}
          <div>
            <div className="flex items-baseline gap-2">
              <h3 className="font-display text-lg font-semibold text-emerald-950">
                Diário de evolução
              </h3>
              {dados.evolucoes.length > 0 && (
                <span className="text-xs text-stone-400">{dados.evolucoes.length}</span>
              )}
            </div>

            {dados.evolucoes.length === 0 ? (
              <p className="mt-2 text-stone-400">Nenhuma anotação ainda.</p>
            ) : (
              <ol className="relative mt-3 ml-1.5 border-l-2 border-stone-200 pl-5">
                {dados.evolucoes.map((e) => (
                  <li key={e.id} className="relative pb-4 last:pb-0">
                    <span className="absolute top-1.5 -left-6.5 h-2.5 w-2.5 rounded-full bg-sky-500 ring-4 ring-white" />
                    <p className="text-xs font-semibold text-stone-500">
                      {isoParaData(e.data)}
                      {e.registrado_por && (
                        <span className="font-normal text-stone-400">
                          {' '}
                          — {e.registrado_por.nome_completo}
                        </span>
                      )}
                    </p>
                    <p className="mt-0.5 leading-relaxed whitespace-pre-line text-stone-700">
                      {e.texto}
                    </p>
                  </li>
                ))}
              </ol>
            )}

            {!concluido && (
              <form onSubmit={adicionarEvolucao} className="mt-4 flex gap-2">
                <input
                  type="text"
                  placeholder="Nova anotação no diário..."
                  value={novaEvolucao}
                  onChange={(e) => setNovaEvolucao(e.target.value)}
                  className="campo flex-1"
                />
                <Botao type="submit" disabled={enviando || !novaEvolucao.trim()}>
                  Anotar
                </Botao>
              </form>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-4">
            <Botao
              variante="fantasma"
              pequeno
              onClick={async () => {
                const { gerarPdfTratamento } = await import('../utils/gerarPdfTratamento')
                gerarPdfTratamento(dados)
              }}
            >
              ⬇ Baixar PDF
            </Botao>
            <div className="flex gap-2">
              <Botao variante="perigo" pequeno onClick={excluir}>
                Excluir
              </Botao>
              {!concluido && (
                <Botao variante="secundario" pequeno onClick={fecharCaso}>
                  Fechar caso
                </Botao>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}
