import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { ResumoDoDia } from '../components/ResumoDoDia'
import {
  Avatar,
  BotaoLink,
  Carregando,
  EstadoVazio,
  MensagemErro,
  Paginacao,
  Pill,
  TituloPagina,
} from '../components/ui'
import { mascaraTelefone } from '../utils/formatadores'

const ROTULO_PAPEL = {
  assistido: 'Assistido(a)',
  trabalhador: 'Trabalhador(a)',
}

export function Pessoas() {
  const [busca, setBusca] = useState('')
  const [papel, setPapel] = useState('')
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    setCarregando(true)
    setErro('')

    const params = new URLSearchParams({ page: pagina, size: 20 })
    if (busca.trim()) params.set('q', busca.trim())
    if (papel) params.set('papel', papel)
    if (incluirInativos) params.set('incluir_inativos', 'true')

    // pequena espera pra não disparar uma busca a cada letra digitada
    const timer = setTimeout(() => {
      api
        .get(`/pessoas?${params}`)
        .then(setDados)
        .catch((e) => setErro(e.message))
        .finally(() => setCarregando(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [busca, papel, incluirInativos, pagina])

  const semFiltro = !busca.trim() && !papel && !incluirInativos

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
        <ResumoDoDia />

        <div className="mt-8">
          <TituloPagina
            titulo="Pessoas"
            subtitulo={
              dados
                ? `${dados.total} ${dados.total === 1 ? 'ficha' : 'fichas'}${
                    semFiltro ? ' ativas' : ' encontradas'
                  }`
                : null
            }
            acoes={<BotaoLink to="/pessoas/nova" variante="primario">+ Nova pessoa</BotaoLink>}
          />
        </div>

        {/* barra de filtros */}
        <div className="mt-5 flex flex-wrap items-center gap-2 rounded-xl bg-white p-2 shadow-sm ring-1 ring-stone-900/5">
          <div className="relative min-w-56 flex-1">
            <IconeBusca className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-stone-400" />
            <input
              type="search"
              placeholder="Buscar por nome, telefone ou CPF..."
              value={busca}
              onChange={(e) => {
                setPagina(1)
                setBusca(e.target.value)
              }}
              className="campo border-transparent bg-stone-50 pl-9 shadow-none focus:bg-white"
            />
          </div>
          <select
            value={papel}
            onChange={(e) => {
              setPagina(1)
              setPapel(e.target.value)
            }}
            className="campo w-auto border-transparent bg-stone-50 shadow-none focus:bg-white"
          >
            <option value="">Todos os papéis</option>
            <option value="assistido">Assistido(a)</option>
            <option value="trabalhador">Trabalhador(a)</option>
          </select>
          <label className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-stone-600 select-none hover:bg-stone-50">
            <input
              type="checkbox"
              checked={incluirInativos}
              onChange={(e) => {
                setPagina(1)
                setIncluirInativos(e.target.checked)
              }}
              className="accent-emerald-700"
            />
            Mostrar inativos
          </label>
        </div>

        <div className="mt-4 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          <MensagemErro className="m-4">{erro}</MensagemErro>

          {!erro && carregando && <Carregando />}

          {!erro && !carregando && dados?.items.length === 0 && (
            <EstadoVazio
              titulo={semFiltro ? 'Nenhuma pessoa cadastrada ainda' : 'Nenhuma pessoa encontrada'}
              descricao={
                semFiltro
                  ? 'Comece cadastrando a primeira ficha.'
                  : 'Tente outra busca ou limpe os filtros.'
              }
              acao={
                semFiltro && (
                  <BotaoLink to="/pessoas/nova" variante="primario">
                    + Nova pessoa
                  </BotaoLink>
                )
              }
            />
          )}

          {!erro && !carregando && dados?.items.length > 0 && (
            <ul className="divide-y divide-stone-100">
              {dados.items.map((p) => (
                <li key={p.id}>
                  <Link
                    to={`/pessoas/${p.id}`}
                    className="group flex items-center gap-4 px-4 py-3 transition hover:bg-emerald-50/50 sm:px-5"
                  >
                    <Avatar nome={p.nome_completo} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-stone-800 group-hover:text-emerald-950">
                        {p.nome_completo}
                      </p>
                      <p className="truncate text-xs text-stone-500">
                        {[
                          p.telefone ? mascaraTelefone(p.telefone) : null,
                          p.cidade ? `${p.cidade}${p.uf ? '/' + p.uf : ''}` : null,
                        ]
                          .filter(Boolean)
                          .join(' · ') || 'sem contato cadastrado'}
                      </p>
                    </div>
                    <div className="hidden shrink-0 flex-wrap justify-end gap-1.5 sm:flex">
                      {p.papeis.map((papelNome) => (
                        <Pill key={papelNome} tom={papelNome === 'trabalhador' ? 'ambar' : 'verde'}>
                          {ROTULO_PAPEL[papelNome] ?? papelNome}
                        </Pill>
                      ))}
                      {!p.ativo && <Pill tom="cinza">inativa</Pill>}
                    </div>
                    <IconeSeta className="h-4 w-4 shrink-0 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-emerald-700" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {dados && <Paginacao pagina={pagina} totalPaginas={dados.pages} aoMudar={setPagina} />}
      </main>
    </div>
  )
}

function IconeBusca({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4-4" strokeLinecap="round" />
    </svg>
  )
}

function IconeSeta({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="m9 6 6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
