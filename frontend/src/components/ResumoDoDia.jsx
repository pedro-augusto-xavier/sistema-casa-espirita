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
    <div className="grid grid-cols-2 gap-3 animate-entrar sm:grid-cols-4">
      <Numero valor={resumo.pessoas} rotulo="pessoas ativas" icone={IconePessoas} />
      <Numero valor={resumo.atendimentosHoje} rotulo="atendimentos hoje" icone={IconeCoracao} />
      <Numero
        valor={resumo.tratamentosAbertos}
        rotulo="tratamentos em andamento"
        icone={IconeFolha}
      />

      <div className="relative overflow-hidden rounded-xl bg-white p-4 shadow-sm ring-1 ring-stone-900/5">
        <span className="absolute inset-y-0 left-0 w-1 bg-linear-to-b from-amber-400 to-amber-600" />
        <div className="flex items-start justify-between gap-2">
          <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
            Próximo evento
          </p>
          <IconeCalendario className="h-5 w-5 text-amber-600" />
        </div>
        {resumo.proximoEvento ? (
          <>
            <p className="mt-2 truncate font-display text-base font-semibold text-emerald-950">
              {resumo.proximoEvento.titulo}
            </p>
            <p className="text-xs text-stone-500">
              {ROTULO_TIPO[resumo.proximoEvento.tipo]} ·{' '}
              {formatarDataHora(resumo.proximoEvento.data_inicio)}
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-stone-400">nada agendado</p>
        )}
      </div>
    </div>
  )
}

function Numero({ valor, rotulo, icone: Icone }) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-white p-4 shadow-sm ring-1 ring-stone-900/5">
      <span className="absolute inset-y-0 left-0 w-1 bg-linear-to-b from-emerald-600 to-emerald-800" />
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
          {rotulo}
        </p>
        <Icone className="h-5 w-5 text-emerald-700" />
      </div>
      <p className="mt-1 font-display text-3xl font-semibold text-emerald-950">{valor}</p>
    </div>
  )
}

// Ícones simples em SVG (traço fino), sem biblioteca externa.

function IconePessoas({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20a6.5 6.5 0 0 1 13 0" strokeLinecap="round" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M15 14.5a5 5 0 0 1 6.5 4.5" strokeLinecap="round" />
    </svg>
  )
}

function IconeCoracao({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path
        d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function IconeFolha({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14Z" strokeLinejoin="round" />
      <path d="M5 19c3-4 6-7 10-10" strokeLinecap="round" />
    </svg>
  )
}

function IconeCalendario({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <rect x="3.5" y="5" width="17" height="15" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" strokeLinecap="round" />
    </svg>
  )
}
