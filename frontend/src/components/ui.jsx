import { Link } from 'react-router-dom'
import { Emblema } from './Emblema'

// Peças pequenas e reutilizáveis da interface. A "cara" dos botões e campos
// vem das classes .btn-* e .campo definidas em src/index.css.

const VARIANTES = {
  primario: 'btn-primario',
  secundario: 'btn-secundario',
  perigo: 'btn-perigo',
  fantasma: 'btn-fantasma',
}

export function Botao({
  variante = 'primario',
  pequeno = false,
  className = '',
  type = 'button',
  children,
  ...resto
}) {
  return (
    <button
      type={type}
      className={`btn ${VARIANTES[variante]} ${pequeno ? 'btn-sm' : ''} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}

export function BotaoLink({
  to,
  variante = 'secundario',
  pequeno = false,
  className = '',
  children,
}) {
  return (
    <Link
      to={to}
      className={`btn ${VARIANTES[variante]} ${pequeno ? 'btn-sm' : ''} ${className}`}
    >
      {children}
    </Link>
  )
}

const TONS_PILL = {
  verde: 'bg-emerald-100 text-emerald-800 ring-emerald-800/10',
  cinza: 'bg-stone-100 text-stone-600 ring-stone-900/10',
  ambar: 'bg-amber-100 text-amber-800 ring-amber-800/10',
  vermelho: 'bg-red-100 text-red-700 ring-red-800/10',
  azul: 'bg-sky-100 text-sky-800 ring-sky-800/10',
}

export function Pill({ tom = 'cinza', className = '', children }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONS_PILL[tom]} ${className}`}
    >
      {children}
    </span>
  )
}

export function iniciais(nome) {
  const partes = (nome || '').trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return (primeira + ultima).toUpperCase()
}

export function Avatar({ nome, className = 'h-10 w-10 text-sm' }) {
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full bg-linear-to-br from-emerald-100 to-emerald-200 font-display font-semibold text-emerald-900 ring-1 ring-emerald-900/10 ${className}`}
    >
      {iniciais(nome)}
    </span>
  )
}

/** Rótulo + controle de formulário. O controle recebe a classe `campo` sozinho. */
export function Campo({ label, obrigatorio = false, dica, className = '', children }) {
  return (
    <label className={`block text-sm font-medium text-stone-700 ${className}`}>
      {label}
      {obrigatorio && <span className="ml-0.5 text-amber-600">*</span>}
      {dica && <span className="ml-1.5 text-xs font-normal text-stone-400">{dica}</span>}
      <div className="mt-1">{children}</div>
    </label>
  )
}

/** Título pequeno em caixa alta, usado dentro de fichas e modais. */
export function Rotulo({ className = '', children }) {
  return (
    <p className={`text-[11px] font-semibold tracking-wider text-stone-400 uppercase ${className}`}>
      {children}
    </p>
  )
}

export function Cartao({ className = '', children }) {
  return <div className={`cartao ${className}`}>{children}</div>
}

/** Cabeçalho de página: título em fonte de destaque + traço verde + ações à direita. */
export function TituloPagina({ titulo, subtitulo, acoes }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="font-display text-2xl font-semibold text-emerald-950 sm:text-3xl">
          {titulo}
        </h2>
        <span className="mt-2 block h-1 w-12 rounded-full bg-linear-to-r from-emerald-700 to-amber-500" />
        {subtitulo && <p className="mt-2 text-sm text-stone-500">{subtitulo}</p>}
      </div>
      {acoes && <div className="flex shrink-0 flex-wrap gap-2">{acoes}</div>}
    </div>
  )
}

export function EstadoVazio({ titulo, descricao, acao }) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      <Emblema className="h-16 w-16 opacity-30 grayscale" />
      <p className="mt-4 font-display text-lg text-stone-700">{titulo}</p>
      {descricao && <p className="mt-1 max-w-sm text-sm text-stone-500">{descricao}</p>}
      {acao && <div className="mt-5">{acao}</div>}
    </div>
  )
}

export function Carregando({ texto = 'Carregando...' }) {
  return (
    <div className="flex items-center gap-3 px-6 py-10 text-sm text-stone-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-emerald-700" />
      {texto}
    </div>
  )
}

export function MensagemErro({ children, className = '' }) {
  if (!children) return null
  return (
    <p
      className={`rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 ${className}`}
    >
      {children}
    </p>
  )
}

/** Barra de paginação (Anterior · Página x de y · Próxima). */
export function Paginacao({ pagina, totalPaginas, aoMudar }) {
  if (!totalPaginas || totalPaginas <= 1) return null
  return (
    <div className="mt-4 flex items-center justify-center gap-3 text-sm text-stone-600">
      <Botao
        variante="secundario"
        pequeno
        disabled={pagina <= 1}
        onClick={() => aoMudar(pagina - 1)}
      >
        ← Anterior
      </Botao>
      <span>
        Página <strong className="text-stone-800">{pagina}</strong> de {totalPaginas}
      </span>
      <Botao
        variante="secundario"
        pequeno
        disabled={pagina >= totalPaginas}
        onClick={() => aoMudar(pagina + 1)}
      >
        Próxima →
      </Botao>
    </div>
  )
}
