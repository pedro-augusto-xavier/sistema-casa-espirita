import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import {
  OPCOES_VINCULO,
  ROTULO_VINCULO,
  dataEstranha,
  dataParaIso,
  hojeIso,
  isoParaData,
  mascaraData,
} from '../utils/formatadores'
import { SeletorPessoa } from './SeletorPessoa'
import { Avatar, Botao, MensagemErro, Pill, Rotulo } from './ui'

/**
 * A pasta de Desobsessão do papel, em cartão. A capa: Responsável (quem
 * vem à casa) e Assistidos (por quem ela pediu — com etiqueta "concluído" quando concluem).
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

/** Linha embaixo do nome de quem concluiu: data, situação final e o "reativar". */
export function StatusConcluido({ assistido, aoReativar }) {
  return (
    <div className="text-xs">
      <p className="flex flex-wrap items-center gap-x-1.5">
        <span className="inline-flex items-center gap-1 font-medium text-emerald-700">
          <IconeCheck className="h-3 w-3" />
          concluído{assistido.data_conclusao && ` em ${isoParaData(assistido.data_conclusao)}`}
        </span>
        {aoReativar && (
          <>
            <span className="text-stone-300">·</span>
            <button
              type="button"
              onClick={aoReativar}
              className="text-stone-400 underline decoration-stone-300 underline-offset-2 transition hover:text-emerald-800 hover:decoration-emerald-600"
            >
              reativar
            </button>
          </>
        )}
      </p>
      {assistido.situacao_final && (
        <p className="mt-0.5 text-stone-500">{assistido.situacao_final}</p>
      )}
    </div>
  )
}

function Icone({ className, children }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {children}
    </svg>
  )
}

function IconeCheck({ className }) {
  return (
    <Icone className={className}>
      <path d="M20 6 9 17l-5-5" />
    </Icone>
  )
}

function IconeX({ className }) {
  return (
    <Icone className={className}>
      <path d="M18 6 6 18M6 6l12 12" />
    </Icone>
  )
}

function IconeLapis({ className }) {
  return (
    <Icone className={className}>
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </Icone>
  )
}

export function FichaCaso({ caso, pessoaId, aoMudar, aoAbrir }) {
  const [nota, setNota] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState('')
  const [adicionando, setAdicionando] = useState(false)
  // data de início sendo corrigida (dd/mm/aaaa) ou null fora da edição
  const [inicio, setInicio] = useState(null)
  const { usuario } = useAuth()

  const concluido = caso.status === 'concluido'
  // caso ligado a ficha anonimizada: só o admin mexe (o servidor também barra)
  const podeEditar =
    !concluido &&
    (usuario.papel === 'admin' ||
      !(caso.solicitante?.anonimizada || caso.assistidos.some((a) => a.pessoa.anonimizada)))
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
        data_conclusao: hojeIso(),
      }),
    )
  }

  function salvarInicio(evento) {
    evento.preventDefault()
    const iso = dataParaIso(inicio)
    if (!iso) return setErro('Data inválida — use o formato dd/mm/aaaa.')
    if (dataEstranha(iso) === 'futuro') return setErro('O início não pode ser no futuro.')
    chamar(async () => {
      await api.patch(`/tratamentos/${caso.id}`, { data_inicio: iso })
      setInicio(null)
    })
  }

  function reativarAssistido(a) {
    if (
      !confirm(
        `Reativar ${a.pessoa.nome_completo}? A data e a situação final da conclusão serão apagadas.`,
      )
    )
      return
    chamar(() =>
      api.patch(`/tratamentos/${caso.id}/assistidos/${a.id}`, {
        status: 'ativo',
        situacao_final: null,
        data_conclusao: null,
      }),
    )
  }

  function adicionarAssistido(p) {
    if (!p) return
    setAdicionando(false)
    chamar(() => api.post(`/tratamentos/${caso.id}/assistidos`, { pessoa_id: p.id }))
  }

  function definirVinculo(assistidoId, vinculo) {
    chamar(() =>
      api.patch(`/tratamentos/${caso.id}/assistidos/${assistidoId}`, {
        vinculo_com_responsavel: vinculo || null,
      }),
    )
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
            <Rotulo>Tratamento</Rotulo>
            <h3 className="mt-0.5 font-display text-2xl font-semibold text-emerald-950">
              {caso.tipo_nome}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <Pill tom={concluido ? 'cinza' : 'ambar'}>
              {concluido ? 'Concluída' : 'Em andamento'}
            </Pill>
            <Botao variante="secundario" pequeno onClick={aoAbrir}>
              Abrir tratamento →
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
                  <li key={a.id} className="flex items-start gap-2">
                    <Avatar
                      nome={a.pessoa.nome_completo}
                      className={`h-7 w-7 shrink-0 text-[10px] ${ativo ? '' : 'grayscale'}`}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex min-h-7 items-center gap-2">
                        <span
                          className={`min-w-0 flex-1 truncate text-sm ${ativo ? '' : 'opacity-60'}`}
                        >
                          <NomePessoa pessoa={a.pessoa} estaFicha={a.pessoa.id === pessoaId} />
                        </span>
                        {a.pessoa.id !== caso.solicitante?.id &&
                          (ativo && podeEditar ? (
                            <select
                              value={a.vinculo_com_responsavel || ''}
                              onChange={(e) => definirVinculo(a.id, e.target.value)}
                              className="shrink-0 rounded-full border-0 bg-stone-100 py-0.5 pr-5 pl-1.5 text-[10px] text-stone-600 outline-none focus:ring-1 focus:ring-emerald-600/40"
                            >
                              <option value="">qual a relação?</option>
                              {OPCOES_VINCULO.map(([valor, rotulo]) => (
                                <option key={valor} value={valor}>
                                  {rotulo}
                                </option>
                              ))}
                            </select>
                          ) : (
                            a.vinculo_com_responsavel && (
                              <Pill tom="cinza" className="shrink-0 text-[10px]">
                                {ROTULO_VINCULO[a.vinculo_com_responsavel]}
                              </Pill>
                            )
                          ))}
                        {ativo && podeEditar && (
                          <button
                            type="button"
                            onClick={() => concluirAssistido(a)}
                            className="text-xs text-stone-400 hover:text-emerald-800 hover:underline"
                          >
                            concluir
                          </button>
                        )}
                      </div>
                      {!ativo && (
                        <StatusConcluido
                          assistido={a}
                          aoReativar={podeEditar ? () => reativarAssistido(a) : null}
                        />
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
            {podeEditar &&
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
            {inicio !== null ? (
              <dd className="mt-0.5">
                <form onSubmit={salvarInicio} className="flex items-center gap-0.5">
                  <input
                    autoFocus
                    inputMode="numeric"
                    placeholder="dd/mm/aaaa"
                    maxLength={10}
                    value={inicio}
                    onChange={(e) => setInicio(mascaraData(e.target.value))}
                    onKeyDown={(e) => e.key === 'Escape' && setInicio(null)}
                    aria-label="Data de início"
                    className="w-26 rounded-md border border-emerald-600/40 bg-white px-1.5 py-0.5 text-sm text-stone-800 ring-2 ring-emerald-600/10 outline-none"
                  />
                  <button
                    type="submit"
                    title="Salvar"
                    aria-label="Salvar data de início"
                    className="rounded-md p-1 text-emerald-700 transition hover:bg-emerald-50"
                  >
                    <IconeCheck className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setInicio(null)}
                    title="Cancelar"
                    aria-label="Cancelar"
                    className="rounded-md p-1 text-stone-400 transition hover:bg-stone-100 hover:text-stone-600"
                  >
                    <IconeX className="h-4 w-4" />
                  </button>
                </form>
              </dd>
            ) : (
              <dd className="group mt-0.5 flex items-center gap-1 text-sm text-stone-800">
                {isoParaData(caso.data_inicio)}
                {podeEditar && (
                  <button
                    type="button"
                    onClick={() => setInicio(isoParaData(caso.data_inicio))}
                    title="Alterar data de início"
                    aria-label="Alterar data de início"
                    className="rounded-md p-1 text-stone-300 transition group-hover:text-stone-500 hover:bg-stone-100 hover:text-emerald-800"
                  >
                    <IconeLapis className="h-3.5 w-3.5" />
                  </button>
                )}
              </dd>
            )}
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

          {podeEditar && (
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
