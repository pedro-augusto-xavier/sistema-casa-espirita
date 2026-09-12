import { useEffect } from 'react'

export function Modal({ titulo, onFechar, largura = 'max-w-lg', children }) {
  // Esc fecha o modal
  useEffect(() => {
    function aoTeclar(e) {
      if (e.key === 'Escape') onFechar()
    }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [onFechar])

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-stone-900/40 p-4 backdrop-blur-sm animate-surgir"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onFechar()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        className={`w-full ${largura} max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl shadow-stone-900/20 ring-1 ring-stone-900/10 animate-entrar`}
      >
        <div className="flex items-start justify-between gap-4">
          {titulo ? (
            <h3 className="font-display text-xl font-semibold text-emerald-950">{titulo}</h3>
          ) : (
            <span />
          )}
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="-mt-1 -mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xl leading-none text-stone-400 transition hover:bg-stone-100 hover:text-stone-700"
          >
            ×
          </button>
        </div>
        <div className={titulo ? 'mt-4' : 'mt-1'}>{children}</div>
      </div>
    </div>
  )
}
