import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { isoParaData } from '../utils/formatadores'
import { SeletorPessoa } from './SeletorPessoa'
import { Avatar, Botao, MensagemErro, Pill, Rotulo } from './ui'

/**
 * A pasta de Desobsessão do papel, em cartão. A capa: Responsável (quem
 * vem à casa) e Assistidos (por quem ela pediu — riscados quando concluem).
 * Dentro: nº de vezes, início, observação, situação final e o diário por
 * data, com a anotação nova direto ali.
 */
/** Nome que leva à ficha da pessoa — menos quando já é a ficha aberta. */
function NomePessoa({ pessoa, estaFicha, className = '' }) {
  if (estaFicha) {
    return (
      <span className={`text-stone-800 ${className}`}>
        {pessoa.nome_completo}
        <span className="ml-1 text-xs font-normal text-stone-400">(esta ficha)</span>
      </span>
    )
  }
  return (
    <Link
      to={`/pessoas/${pessoa.id}`}
      className={`text-stone-800 underline decoration-stone-300 underline-offset-2 transition hover:text-emerald-800 hover:decoration-emerald-600 ${className}`}
    >
      {pessoa.nome_completo}
    </Link>
  )
}

export function FichaCaso({ caso, pessoaId, aoMudar, aoAbrir }) {
  const [nota, setNota] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState('')
  const [adicionando, setAdicionando] = useState(false)

  const concluido = caso.status === 'concluido'
  const previstas = caso.sessoes_previstas
  const feitas = caso.sessoes_realizadas ?? 0
  const progresso = previstas ? Math.min(100, Math.round((feitas / previstas) * 100)) : null
  const souResponsavel = caso.solicitante?.id === pessoaId

  async function chamar(fn) {
    setErro('')
    try {
      await fn()
      aoMudar()
    } catch (e) {
      setErro(e.message)
    }
  }

  async function anotar(evento) {
    evento.preventDefault()
    if (!nota.trim()) return
    setEnviando(true)
    await chamar(async () => {
      await api.post(`/tratamentos/${caso.id}/evolucoes`, { texto: nota.trim() })
      setNota('')
    })
    setEnviando(false)
  }

  function concluirAssistido(a) {
    const situacao = prompt(`Situação final de ${a.pessoa.nome_completo} (opcional):`)
    if (situacao === null) return
    chamar(() =>
      api.patch(`/tratamentos/${caso.id}/assistidos/${a.id}`, {
        status: 'concluido',
        situacao_final: situacao || null,
        data_conclusao: new Date().toISOString().slice(0, 10),
      }),
    )
  }

  function adicionarAssistido(p) {
    if (!p) return
    setAdicionando(false)
    chamar(() => api.post(`/tratamentos/${caso.id}/assistidos`, { pessoa_id: p.id }))
  }

  return (
    <article
      className={`overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-stone-900/5 ${
        concluido ? 'opacity-80' : ''
      }`}
    >
      <div
        className={`h-1.5 ${concluido ? 'bg-stone-300' : 'bg-linear-to-r from-amber-500 to-amber-300'}`}
      />

      <div className="p-5 sm:p-6">
        {/* ---------- capa ---------- */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Rotulo>Pasta de acompanhamento</Rotulo>
            <h3 className="mt-0.5 font-display text-2xl font-semibold text-emerald-950">
              {caso.tipo_nome}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <Pill tom={concluido ? 'cinza' : 'ambar'}>
              {concluido ? 'Concluída' : 'Em andamento'}
            </Pill>
            <Botao variante="secundario" pequeno onClick={aoAbrir}>
              Abrir pasta →
            </Botao>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <Rotulo>Responsável</Rotulo>
            <p className="mt-1 text-xs text-stone-400">quem vem à casa receber o tratamento</p>
            {caso.solicitante ? (
              <div className="mt-2 flex items-center gap-2">
                <Avatar nome={caso.solicitante.nome_completo} className="h-8 w-8 text-xs" />
                <NomePessoa pessoa={caso.solicitante} estaFicha={souResponsavel} className="font-medium" />
              </div>
            ) : (
              <p className="mt-2 text-sm text-stone-300">—</p>
            )}
          </div>

          <div>
            <Rotulo>Assistidos</Rotulo>
            <p className="mt-1 text-xs text-stone-400">por quem pediu — filhos, amigos, ela mesma</p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {caso.assistidos.map((a) => {
                const ativo = a.status === 'ativo'
                return (
                  <li key={a.id} className="flex items-center gap-2">
                    <Avatar
                      nome={a.pessoa.nome_completo}
                      className={`h-7 w-7 text-[10px] ${ativo ? '' : 'grayscale'}`}
                    />
                    <span
                      className={`min-w-0 flex-1 truncate text-sm ${
                        ativo ? '' : 'line-through decoration-stone-400'
                      }`}
                      title={a.situacao_final || undefined}
                    >
                      <NomePessoa
                        pessoa={a.pessoa}
                        estaFicha={a.pessoa.id === pessoaId}
                        className={ativo ? '' : 'text-stone-400'}
                      />
                    </span>
                    {!ativo && a.data_conclusao && (
                      <span className="text-[10px] text-stone-400">{isoParaData(a.data_conclusao)}</span>
                    )}
                    {ativo && !concluido && (
                      <button
                        type="button"
                        onClick={() => concluirAssistido(a)}
                        className="text-xs text-stone-400 hover:text-emerald-800 hover:underline"
                      >
                        concluir
                      </button>
                    )}
                  </li>
                )
              })}
            </ul>
            {!concluido &&
              (adicionando ? (
                <div className="mt-2">
                  <SeletorPessoa
                    valor={null}
                    aoSelecionar={adicionarAssistido}
                    placeholder="Buscar ou cadastrar pessoa..."
                    permitirCadastro
                  />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setAdicionando(true)}
                  className="mt-2 text-xs text-stone-400 hover:text-emerald-800 hover:underline"
                >
                  + adicionar assistido
                </button>
              ))}
          </div>
        </div>

        {/* ---------- dentro da pasta ---------- */}
        <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-dashed border-stone-200 pt-4 sm:grid-cols-3">
          <div>
            <Rotulo>Início</Rotulo>
            <dd className="mt-0.5 text-sm text-stone-800">{isoParaData(caso.data_inicio)}</dd>
          </div>
          <div className="col-span-2 sm:col-span-2">
            <Rotulo>Nº de vezes</Rotulo>
            <dd className="mt-0.5 flex items-center gap-3">
              <span className="font-display text-2xl leading-none font-semibold text-emerald-950">
                {feitas}
                {previstas ? (
                  <span className="text-base font-normal text-stone-400"> / {previstas}</span>
                ) : null}
              </span>
              {progresso !== null && (
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-stone-100">
                  <span
                    className={`block h-full rounded-full ${progresso >= 100 ? 'bg-emerald-600' : 'bg-amber-500'}`}
                    style={{ width: `${progresso}%` }}
                  />
                </span>
              )}
            </dd>
          </div>
        </dl>

        {caso.observacao && (
          <div className="mt-4">
            <Rotulo className="mb-1">Observação</Rotulo>
            <p className="rounded-lg border-l-4 border-amber-400 bg-amber-50/70 px-3 py-2 text-[15px] leading-relaxed whitespace-pre-line text-stone-800">
              {caso.observacao}
            </p>
          </div>
        )}

        {caso.situacao_final && (
          <div className="mt-4">
            <Rotulo className="mb-1">Situação final</Rotulo>
            <p className="rounded-lg bg-stone-50 px-3 py-2 text-sm leading-relaxed text-stone-700 ring-1 ring-stone-900/5">
              {caso.situacao_final}
            </p>
          </div>
        )}

        {/* ---------- diário ---------- */}
        <div className="mt-5 border-t border-dashed border-stone-200 pt-4">
          <Rotulo className="mb-2">Diário</Rotulo>
          {caso.evolucoes.length === 0 ? (
            <p className="text-sm text-stone-400">Nenhuma anotação ainda.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {caso.evolucoes.map((e) => (
                <li key={e.id} className="flex gap-3 text-[15px] leading-relaxed">
                  <span className="shrink-0 font-semibold text-emerald-950 tabular-nums">
                    {isoParaData(e.data)}
                  </span>
                  <span className="text-stone-400">—</span>
                  <span className="whitespace-pre-line text-stone-800">
                    {e.texto}
                    {e.registrado_por && (
                      <span className="text-xs text-stone-400">
                        {' '}
                        ({e.registrado_por.nome_completo})
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {!concluido && (
            <form onSubmit={anotar} className="mt-3 flex gap-2">
              <input
                type="text"
                placeholder="Anotar no diário (ex: limpeza + doação + 3 choques)"
                value={nota}
                onChange={(e) => setNota(e.target.value)}
                className="campo flex-1"
              />
              <Botao type="submit" pequeno disabled={enviando || !nota.trim()}>
                Anotar
              </Botao>
            </form>
          )}
          <MensagemErro className="mt-2">{erro}</MensagemErro>
        </div>
      </div>
    </article>
  )
}
