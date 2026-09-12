import { useEffect, useState } from 'react'
import { api } from '../api/client'

const ROTULO_TIPO = {
  trabalho: 'Trabalho',
  palestra: 'Palestra',
  grupo: 'Grupo',
  outro: 'Evento',
}

function formatarDataHora(iso) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Faixa de números rápidos: pessoas, atendimentos de hoje, tratamentos abertos, próximo evento. */
export function ResumoDoDia() {
  const [resumo, setResumo] = useState(null)

  useEffect(() => {
    const hoje = new Date().toISOString().slice(0, 10)
    const agora = new Date().toISOString()

    Promise.all([
      api.get('/pessoas?size=1'),
      api.get(`/atendimentos?de=${hoje}&ate=${hoje}&size=1`),
      api.get('/tratamentos?status=em_andamento&size=1'),
      api.get(`/agenda?de=${agora}&size=1`),
    ])
      .then(([pessoas, atendimentos, tratamentos, agenda]) => {
        setResumo({
          pessoas: pessoas.total,
          atendimentosHoje: atendimentos.total,
          tratamentosAbertos: tratamentos.total,
          proximoEvento: agenda.items[0] ?? null,
        })
      })
      .catch(() => setResumo(null))
  }, [])

  if (!resumo) return null

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Cartao numero={resumo.pessoas} rotulo="pessoas ativas" />
      <Cartao numero={resumo.atendimentosHoje} rotulo="atendimentos hoje" />
      <Cartao numero={resumo.tratamentosAbertos} rotulo="tratamentos em andamento" />
      <div className="rounded-lg border-t-2 border-amber-500 bg-white p-4 shadow-sm ring-1 ring-stone-900/5">
        <p className="text-xs font-medium uppercase tracking-wide text-stone-400">
          Próximo evento
        </p>
        {resumo.proximoEvento ? (
          <>
            <p className="mt-1 truncate text-sm font-semibold text-emerald-900">
              {resumo.proximoEvento.titulo}
            </p>
            <p className="text-xs text-stone-500">
              {ROTULO_TIPO[resumo.proximoEvento.tipo]} ·{' '}
              {formatarDataHora(resumo.proximoEvento.data_inicio)}
            </p>
          </>
        ) : (
          <p className="mt-1 text-sm text-stone-400">nada agendado</p>
        )}
      </div>
    </div>
  )
}

function Cartao({ numero, rotulo }) {
  return (
    <div className="rounded-lg border-t-2 border-emerald-700 bg-white p-4 shadow-sm ring-1 ring-stone-900/5">
      <p className="font-display text-2xl font-semibold text-emerald-900">{numero}</p>
      <p className="text-xs font-medium uppercase tracking-wide text-stone-400">
        {rotulo}
      </p>
    </div>
  )
}
