export function Modal({ titulo, onFechar, children }) {
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800">{titulo}</h3>
          <button
            type="button"
            onClick={onFechar}
            className="text-xl leading-none text-slate-400 hover:text-slate-600"
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
