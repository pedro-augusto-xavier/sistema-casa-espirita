import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Avatar } from './ui'

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
      <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/60 py-1.5 pr-2 pl-2 text-sm">
        <Avatar nome={valor.nome_completo} className="h-7 w-7 text-[10px]" />
        <span className="min-w-0 flex-1 truncate font-medium text-emerald-950">
          {valor.nome_completo}
        </span>
        <button
          type="button"
          onClick={() => aoSelecionar(null)}
          className="rounded-md px-2 py-1 text-xs text-stone-500 transition hover:bg-white hover:text-stone-800"
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
        className="campo"
      />
      {aberto && opcoes.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-xl bg-white p-1 text-sm shadow-lg ring-1 ring-stone-900/10 animate-surgir">
          {opcoes.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => {
                  aoSelecionar(p)
                  setBusca('')
                  setAberto(false)
                }}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-emerald-50"
              >
                <Avatar nome={p.nome_completo} className="h-7 w-7 text-[10px]" />
                <span className="min-w-0 flex-1 truncate text-stone-800">{p.nome_completo}</span>
                {p.cidade && (
                  <span className="shrink-0 text-xs text-stone-400">{p.cidade}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
      {aberto && busca.trim() && opcoes.length === 0 && (
        <p className="absolute z-10 mt-1 w-full rounded-xl bg-white px-3 py-2 text-xs text-stone-400 shadow-lg ring-1 ring-stone-900/10">
          Ninguém encontrado com esse nome.
        </p>
      )}
    </div>
  )
}
