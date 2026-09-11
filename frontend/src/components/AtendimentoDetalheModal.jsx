import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { AtendimentoModal } from './AtendimentoModal'
import { Modal } from './Modal'

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
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!erro && !dados && <p className="text-sm text-slate-500">Carregando...</p>}

      {dados && (
        <div className="flex flex-col gap-5 text-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold uppercase tracking-wide text-slate-800">
                Atendimento
              </h2>
              <p className="text-slate-500">
                {isoParaData(dados.data)} · {ROTULO_MODALIDADE[dados.modalidade]}
              </p>
            </div>
            <button
              onClick={() => setEditando(true)}
              className="rounded-md border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
            >
              Editar
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 border-y border-slate-200 py-3">
            <Campo label="Atendido por" valor={dados.atendido_por?.nome_completo} />
            <Campo label="Solicitante" valor={dados.solicitante?.nome_completo} />
            <Campo label="Presente" valor={dados.presente ? 'Sim' : 'Não'} />
            <Campo label="Retorno previsto" valor={isoParaData(dados.retorno_previsto)} />
          </div>

          {dados.observacao && <Secao titulo="Observação">{dados.observacao}</Secao>}

          <Secao titulo="Tratamentos">
            {dados.tratamentos.length === 0 ? (
              <p className="text-slate-500">Nenhum tratamento marcado.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {dados.tratamentos.map((t) => (
                  <li key={t.id}>
                    <p className="font-medium text-slate-700">
                      {t.tipo_tratamento_nome}
                      {t.modalidade && (
                        <span className="ml-2 text-xs font-normal text-slate-500">
                          ({ROTULO_MODALIDADE[t.modalidade]})
                        </span>
                      )}
                    </p>
                    {(t.sessoes_previstas || t.sessoes_realizadas > 0) && (
                      <p className="text-xs text-slate-500">
                        Sessões: {t.sessoes_realizadas}
                        {t.sessoes_previstas ? ` de ${t.sessoes_previstas}` : ''}
                      </p>
                    )}
                    {t.observacao && (
                      <p className="text-xs text-slate-600">{t.observacao}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
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
