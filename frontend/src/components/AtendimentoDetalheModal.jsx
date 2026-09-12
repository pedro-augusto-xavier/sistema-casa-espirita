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
          {/* cabeçalho no estilo da folha de papel, com o PDF logo à mão */}
          <div className="flex flex-wrap items-start justify-between gap-3 border-b-2 border-emerald-900/80 pb-4">
            <div>
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
            <Botao
              onClick={async () => {
                const { gerarPdfAtendimento } = await import('../utils/gerarPdfAtendimento')
                gerarPdfAtendimento(dados)
              }}
            >
              <IconeBaixar className="h-4 w-4" />
              Baixar PDF
            </Botao>
          </div>

          {/* a observação é o que mais importa: vem primeiro e em destaque */}
          <div>
            <Rotulo className="mb-1.5">Observação</Rotulo>
            {dados.observacao ? (
              <p className="rounded-xl border-l-4 border-amber-400 bg-amber-50/70 px-4 py-3 text-base leading-relaxed whitespace-pre-line text-stone-800">
                {dados.observacao}
              </p>
            ) : (
              <p className="text-stone-400">Nenhuma observação registrada.</p>
            )}
          </div>

          <div>
            <Rotulo className="mb-1.5">Tratamentos do dia</Rotulo>
            {dados.tratamentos.length === 0 ? (
              <p className="text-stone-400">Nenhum tratamento marcado.</p>
            ) : (
              <ul className="flex flex-wrap gap-1.5">
                {dados.tratamentos.map((t) => (
                  <li key={t.id}>
                    <Pill tom="verde" className="text-sm">
                      {t.tipo_tratamento_nome}
                      {t.sessoes_previstas ? ` · ${t.sessoes_previstas}x` : ''}
                    </Pill>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 rounded-xl bg-stone-50 p-4 ring-1 ring-stone-900/5">
            <Campo label="Atendido por" valor={dados.atendido_por?.nome_completo} />
            <Campo label="Solicitante" valor={dados.solicitante?.nome_completo} />
            {dados.retorno_previsto && (
              <Campo label="Retorno previsto" valor={isoParaData(dados.retorno_previsto)} />
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-4">
            <Botao variante="perigo" pequeno onClick={excluir}>
              Excluir
            </Botao>
            <Botao variante="secundario" pequeno onClick={() => setEditando(true)}>
              ✎ Editar
            </Botao>
          </div>
        </div>
      )}
    </Modal>
  )
}

function IconeBaixar({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M12 4v11m0 0 4-4m-4 4-4-4M5 19h14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
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
