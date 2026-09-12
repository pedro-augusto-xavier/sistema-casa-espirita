export function Modal({ titulo, onFechar, children }) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg ring-1 ring-stone-900/10">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-lg font-semibold text-emerald-900">{titulo}</h3>
          <button
            type="button"
            onClick={onFechar}
            className="text-xl leading-none text-stone-400 hover:text-stone-600"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  )
}
