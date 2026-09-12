import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { AtendimentoModal } from './AtendimentoModal'
import { Modal } from './Modal'
import { Botao, Carregando, MensagemErro, Pill, Rotulo } from './ui'

const ROTULO_MODALIDADE = {
  presencial: 'Presencial',
  video: 'Vídeo',
  distancia: 'À distância',
}

export function AtendimentoDetalheModal({ atendimentoId, onFechar }) {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [editando, setEditando] = useState(false)

  useEffect(() => {
    carregar()
  }, [atendimentoId])

  function carregar() {
    api
      .get(`/atendimentos/${atendimentoId}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }

  async function excluir() {
    if (!confirm('Excluir este atendimento? Não pode ser desfeito.')) return
    try {
      await api.del(`/atendimentos/${atendimentoId}`)
      onFechar()
    } catch (e) {
      setErro(e.message)
    }
  }

  if (editando && dados) {
    return (
      <AtendimentoModal
        existente={dados}
        onFechar={() => setEditando(false)}
        onSalvo={() => {
          setEditando(false)
          carregar()
        }}
      />
    )
  }

  return (
    <Modal titulo="" onFechar={onFechar}>
      <MensagemErro>{erro}</MensagemErro>
      {!erro && !dados && <Carregando />}

      {dados && (
        <div className="flex flex-col gap-5 text-sm">
          {/* cabeçalho no estilo da folha de papel */}
          <div className="border-b-2 border-emerald-900/80 pb-4">
            <Rotulo>Atendimento</Rotulo>
            <p className="mt-1 font-display text-3xl font-semibold text-emerald-950">
              {isoParaData(dados.data)}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <Pill tom="verde">{ROTULO_MODALIDADE[dados.modalidade]}</Pill>
              <Pill tom={dados.presente ? 'cinza' : 'ambar'}>
                {dados.presente ? 'Presente' : 'Não esteve presente'}
              </Pill>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Campo label="Atendido por" valor={dados.atendido_por?.nome_completo} />
            <Campo label="Solicitante" valor={dados.solicitante?.nome_completo} />
            {dados.retorno_previsto && (
              <Campo label="Retorno previsto" valor={isoParaData(dados.retorno_previsto)} />
            )}
          </div>

          <div>
            <Rotulo className="mb-1.5">Tratamentos</Rotulo>
            {dados.tratamentos.length === 0 ? (
              <p className="text-stone-400">Nenhum tratamento marcado.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {dados.tratamentos.map((t) => (
                  <li key={t.id} className="rounded-lg bg-stone-50 px-3 py-2 ring-1 ring-stone-900/5">
                    <p className="font-medium text-stone-800">
                      {t.tipo_tratamento_nome}
                      {t.modalidade && (
                        <span className="ml-2 text-xs font-normal text-stone-500">
                          {ROTULO_MODALIDADE[t.modalidade]}
                        </span>
                      )}
                    </p>
                    {(t.sessoes_previstas || t.sessoes_realizadas > 0) && (
                      <p className="text-xs text-stone-500">
                        Sessões: {t.sessoes_realizadas}
                        {t.sessoes_previstas ? ` de ${t.sessoes_previstas}` : ''}
                      </p>
                    )}
                    {t.observacao && <p className="mt-1 text-xs text-stone-600">{t.observacao}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {dados.observacao && (
            <div>
              <Rotulo className="mb-1.5">Observação</Rotulo>
              <p className="rounded-xl border-l-4 border-amber-400 bg-amber-50/60 p-3 leading-relaxed whitespace-pre-line text-stone-700">
                {dados.observacao}
              </p>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-4">
            <Botao
              variante="fantasma"
              pequeno
              onClick={async () => {
                const { gerarPdfAtendimento } = await import('../utils/gerarPdfAtendimento')
                gerarPdfAtendimento(dados)
              }}
            >
              ⬇ Baixar PDF
            </Botao>
            <div className="flex gap-2">
              <Botao variante="perigo" pequeno onClick={excluir}>
                Excluir
              </Botao>
              <Botao pequeno onClick={() => setEditando(true)}>
                Editar
              </Botao>
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}

function Campo({ label, valor }) {
  return (
    <div>
      <Rotulo>{label}</Rotulo>
      <p className="mt-0.5 text-stone-800">{valor || <span className="text-stone-300">—</span>}</p>
    </div>
  )
}
