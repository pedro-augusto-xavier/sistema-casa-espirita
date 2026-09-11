import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { Modal } from './Modal'

const ROTULO_MODALIDADE = {
  presencial: 'Presencial',
  video: 'Vídeo',
  distancia: 'À distância',
}

export function AtendimentoDetalheModal({ atendimentoId, onFechar }) {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/atendimentos/${atendimentoId}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [atendimentoId])

  return (
    <Modal titulo="Atendimento" onFechar={onFechar}>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!erro && !dados && <p className="text-sm text-slate-500">Carregando...</p>}

      {dados && (
        <div className="flex flex-col gap-4 text-sm">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
            <Item label="Data" valor={isoParaData(dados.data)} />
            <Item label="Modalidade" valor={ROTULO_MODALIDADE[dados.modalidade]} />
            <Item label="Atendido por" valor={dados.atendido_por?.nome_completo} />
            <Item label="Solicitante" valor={dados.solicitante?.nome_completo} />
            <Item label="Presente" valor={dados.presente ? 'Sim' : 'Não'} />
            <Item label="Retorno previsto" valor={isoParaData(dados.retorno_previsto)} />
          </dl>

          {dados.observacao && (
            <div>
              <p className="text-xs font-medium text-slate-400">Observação</p>
              <p className="text-slate-700">{dados.observacao}</p>
            </div>
          )}

          <div>
            <p className="mb-2 text-xs font-medium text-slate-400">
              Tratamentos do dia
            </p>
            {dados.tratamentos.length === 0 ? (
              <p className="text-slate-500">Nenhum tratamento marcado.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {dados.tratamentos.map((t) => (
                  <li key={t.id} className="rounded-md bg-slate-50 p-2">
                    <p className="font-medium text-slate-700">
                      {t.tipo_tratamento_nome}
                      {t.modalidade && (
                        <span className="ml-2 text-xs text-slate-500">
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
      <dd className="text-slate-700">{valor || '—'}</dd>
    </div>
  )
}
