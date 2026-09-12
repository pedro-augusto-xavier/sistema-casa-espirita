import { useEffect, useState } from 'react'
import { api } from '../api/client'

/** Campo de busca com autocomplete pra escolher uma pessoa já cadastrada. */
export function SeletorPessoa({ valor, aoSelecionar, papel, placeholder = 'Buscar pessoa...' }) {
  const [busca, setBusca] = useState('')
  const [opcoes, setOpcoes] = useState([])
  const [aberto, setAberto] = useState(false)

  useEffect(() => {
    if (!busca.trim()) {
      setOpcoes([])
      return
    }
    const params = new URLSearchParams({ q: busca, size: '8' })
    if (papel) params.set('papel', papel)

    const timer = setTimeout(() => {
      api
        .get(`/pessoas?${params}`)
        .then((d) => setOpcoes(d.items))
        .catch(() => setOpcoes([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [busca, papel])

  if (valor) {
    return (
      <div className="flex items-center justify-between rounded-md border border-stone-300 px-3 py-2 text-sm">
        <span>{valor.nome_completo}</span>
        <button
          type="button"
          onClick={() => aoSelecionar(null)}
          className="text-stone-400 hover:text-stone-600"
        >
          Trocar
        </button>
      </div>
    )
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={busca}
        placeholder={placeholder}
        onChange={(e) => {
          setBusca(e.target.value)
          setAberto(true)
        }}
        onFocus={() => setAberto(true)}
        onBlur={() => setTimeout(() => setAberto(false), 150)}
        className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
      />
      {aberto && opcoes.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border border-stone-200 bg-white text-sm shadow-lg ring-1 ring-stone-900/10">
          {opcoes.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => {
                  aoSelecionar(p)
                  setBusca('')
                  setAberto(false)
                }}
                className="block w-full px-3 py-2 text-left hover:bg-stone-50"
              >
                {p.nome_completo}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
