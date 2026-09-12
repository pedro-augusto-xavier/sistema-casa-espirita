import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, mascaraData, mascaraTelefone } from '../utils/formatadores'
import { Avatar, Botao, MensagemErro } from './ui'

/**
 * Campo de busca com autocomplete pra escolher uma pessoa já cadastrada.
 * Com `permitirCadastro`, oferece um cadastro rápido (só nome obrigatório)
 * quando a pessoa ainda não existe — pra filho, amigo, pai que a
 * responsável menciona na hora e ninguém tem o CPF à mão.
 */
export function SeletorPessoa({
  valor,
  aoSelecionar,
  papel,
  placeholder = 'Buscar pessoa...',
  permitirCadastro = false,
}) {
  const [busca, setBusca] = useState('')
  const [opcoes, setOpcoes] = useState([])
  const [aberto, setAberto] = useState(false)
  const [cadastrando, setCadastrando] = useState(false)

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

  if (cadastrando) {
    return (
      <CadastroRapido
        nomeInicial={busca.trim()}
        aoCancelar={() => setCadastrando(false)}
        aoCriar={(p) => {
          setCadastrando(false)
          setBusca('')
          aoSelecionar(p)
        }}
      />
    )
  }

  const temBusca = busca.trim().length > 0

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
      {aberto && temBusca && (opcoes.length > 0 || permitirCadastro) && (
        <ul
          onMouseDown={(e) => e.preventDefault()} // não rouba o foco do input
          className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-xl bg-white p-1 text-sm shadow-lg ring-1 ring-stone-900/10 animate-surgir"
        >
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
          {opcoes.length === 0 && (
            <li className="px-3 py-2 text-xs text-stone-400">Ninguém encontrado com esse nome.</li>
          )}
          {permitirCadastro && (
            <li className={opcoes.length > 0 ? 'mt-1 border-t border-stone-100 pt-1' : ''}>
              <button
                type="button"
                onClick={() => {
                  setCadastrando(true)
                  setAberto(false)
                }}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-emerald-800 transition hover:bg-emerald-50"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-base leading-none font-semibold">
                  +
                </span>
                <span>
                  Cadastrar <strong>“{busca.trim()}”</strong> como pessoa nova
                </span>
              </button>
            </li>
          )}
        </ul>
      )}
      {aberto && temBusca && opcoes.length === 0 && !permitirCadastro && (
        <p className="absolute z-10 mt-1 w-full rounded-xl bg-white px-3 py-2 text-xs text-stone-400 shadow-lg ring-1 ring-stone-900/10">
          Ninguém encontrado com esse nome.
        </p>
      )}
    </div>
  )
}

/** Formulário mínimo: só o nome é obrigatório. O resto completa-se na ficha. */
function CadastroRapido({ nomeInicial, aoCancelar, aoCriar }) {
  const [nome, setNome] = useState(nomeInicial)
  const [nascimento, setNascimento] = useState('')
  const [sexo, setSexo] = useState('')
  const [telefone, setTelefone] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function criar() {
    setErro('')
    if (nome.trim().length < 3) {
      setErro('Escreva o nome completo.')
      return
    }
    let nascIso = null
    if (nascimento) {
      nascIso = dataParaIso(nascimento)
      if (!nascIso) {
        setErro('Data de nascimento inválida — use dd/mm/aaaa.')
        return
      }
    }
    setEnviando(true)
    try {
      const pessoa = await api.post('/pessoas', {
        nome_completo: nome.trim(),
        data_nascimento: nascIso,
        sexo: sexo || 'nao_informado',
        telefone: telefone || null,
        papeis: ['assistido'],
      })
      aoCriar(pessoa)
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-3 animate-surgir">
      <p className="text-[11px] font-semibold tracking-wider text-emerald-800 uppercase">
        Cadastro rápido
      </p>
      <p className="mt-0.5 text-xs text-stone-500">
        Só o nome é obrigatório. CPF, endereço e o resto podem ser completados depois na ficha.
      </p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <input
          autoFocus
          placeholder="Nome completo *"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), criar())}
          className="campo col-span-2"
        />
        <input
          inputMode="numeric"
          placeholder="Nascimento dd/mm/aaaa"
          maxLength={10}
          value={nascimento}
          onChange={(e) => setNascimento(mascaraData(e.target.value))}
          className="campo"
        />
        <select value={sexo} onChange={(e) => setSexo(e.target.value)} className="campo">
          <option value="">Sexo</option>
          <option value="feminino">Feminino</option>
          <option value="masculino">Masculino</option>
          <option value="outro">Outro</option>
        </select>
        <input
          inputMode="numeric"
          placeholder="Telefone (opcional)"
          maxLength={15}
          value={telefone}
          onChange={(e) => setTelefone(mascaraTelefone(e.target.value))}
          className="campo col-span-2"
        />
      </div>
      <MensagemErro className="mt-2">{erro}</MensagemErro>
      <div className="mt-3 flex justify-end gap-2">
        <Botao variante="fantasma" pequeno onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao pequeno onClick={criar} disabled={enviando}>
          {enviando ? 'Cadastrando...' : 'Cadastrar e usar'}
        </Botao>
      </div>
    </div>
  )
}
