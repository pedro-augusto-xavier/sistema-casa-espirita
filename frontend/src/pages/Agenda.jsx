import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { AgendaModal } from '../components/AgendaModal'
import { Cabecalho } from '../components/Cabecalho'
import {
  Botao,
  Carregando,
  EstadoVazio,
  MensagemErro,
  Paginacao,
  Pill,
  TituloPagina,
} from '../components/ui'

const ROTULO_TIPO = {
  trabalho: 'Trabalho',
  palestra: 'Palestra',
  grupo: 'Grupo',
  outro: 'Outro',
}

const TOM_TIPO = {
  trabalho: 'verde',
  palestra: 'ambar',
  grupo: 'azul',
  outro: 'cinza',
}

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export function Agenda() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [tipo, setTipo] = useState('')
  const [pagina, setPagina] = useState(1)
  const [modalAberto, setModalAberto] = useState(false)
  const [editando, setEditando] = useState(null)
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    const params = new URLSearchParams({ page: pagina, size: 20 })
    if (tipo) params.set('tipo', tipo)
    api
      .get(`/agenda?${params}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [tipo, pagina, versao])

  function aoSalvar() {
    setModalAberto(false)
    setEditando(null)
    setVersao((v) => v + 1)
  }

  async function excluir(id, evento) {
    evento.stopPropagation()
    if (!confirm('Excluir este evento da agenda?')) return
    try {
      await api.del(`/agenda/${id}`)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <TituloPagina
          titulo="Agenda"
          subtitulo="Trabalhos, palestras e grupos — com a escala de quem participa."
          acoes={<Botao onClick={() => setModalAberto(true)}>+ Novo evento</Botao>}
        />

        {/* filtro por tipo, em forma de "chips" */}
        <div className="mt-5 flex flex-wrap gap-1.5">
          <Chip ativo={tipo === ''} onClick={() => { setPagina(1); setTipo('') }}>
            Todos
          </Chip>
          {Object.entries(ROTULO_TIPO).map(([valor, rotulo]) => (
            <Chip
              key={valor}
              ativo={tipo === valor}
              onClick={() => {
                setPagina(1)
                setTipo(valor)
              }}
            >
              {rotulo}
            </Chip>
          ))}
        </div>

        <MensagemErro className="mt-4">{erro}</MensagemErro>

        <div className="mt-4 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!dados ? (
            <Carregando />
          ) : dados.items.length === 0 ? (
            <EstadoVazio
              titulo="Nada na agenda"
              descricao={
                tipo
                  ? 'Nenhum evento desse tipo. Tente outro filtro.'
                  : 'Cadastre o próximo trabalho, palestra ou reunião de grupo.'
              }
              acao={!tipo && <Botao onClick={() => setModalAberto(true)}>+ Novo evento</Botao>}
            />
          ) : (
            <ul className="divide-y divide-stone-100">
              {dados.items.map((ev) => (
                <li key={ev.id}>
                  <button
                    type="button"
                    onClick={() => setEditando(ev.id)}
                    className="group flex w-full items-center gap-4 px-4 py-3 text-left transition hover:bg-emerald-50/50 sm:px-5"
                  >
                    <DataHora iso={ev.data_inicio} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-stone-800 group-hover:text-emerald-950">
                        {ev.titulo}
                      </p>
                      <p className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                        <Pill tom={TOM_TIPO[ev.tipo] ?? 'cinza'}>{ROTULO_TIPO[ev.tipo]}</Pill>
                        <span>
                          {ev.qtd_escalados === 0
                            ? 'ninguém escalado'
                            : `${ev.qtd_escalados} ${ev.qtd_escalados === 1 ? 'pessoa escalada' : 'pessoas escaladas'}`}
                        </span>
                      </p>
                    </div>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => excluir(ev.id, e)}
                      onKeyDown={(e) => e.key === 'Enter' && excluir(ev.id, e)}
                      className="rounded-lg px-2 py-1 text-xs text-stone-400 opacity-0 transition group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 focus:opacity-100"
                    >
                      Excluir
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {dados && <Paginacao pagina={pagina} totalPaginas={dados.pages} aoMudar={setPagina} />}
      </main>

      {modalAberto && <AgendaModal onFechar={() => setModalAberto(false)} onSalvo={aoSalvar} />}
      {editando && (
        <DetalheEvento id={editando} onFechar={() => setEditando(null)} onSalvo={aoSalvar} />
      )}
    </div>
  )
}

function Chip({ ativo, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-sm transition ${
        ativo
          ? 'bg-emerald-800 font-medium text-white shadow-sm'
          : 'bg-white text-stone-600 ring-1 ring-stone-900/10 hover:bg-stone-50'
      }`}
    >
      {children}
    </button>
  )
}

function DataHora({ iso }) {
  const d = new Date(iso)
  const passado = d < new Date()
  return (
    <div
      className={`flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-lg ring-1 ring-stone-900/5 ${
        passado ? 'bg-stone-100' : 'bg-amber-50'
      }`}
    >
      <span className="font-display text-lg leading-none font-semibold text-emerald-950">
        {String(d.getDate()).padStart(2, '0')}
      </span>
      <span className="mt-0.5 text-[10px] leading-none tracking-wider text-stone-500 uppercase">
        {MESES[d.getMonth()]}
      </span>
      <span className="mt-1 text-[10px] leading-none text-stone-400">
        {String(d.getHours()).padStart(2, '0')}:{String(d.getMinutes()).padStart(2, '0')}
      </span>
    </div>
  )
}

function DetalheEvento({ id, onFechar, onSalvo }) {
  const [existente, setExistente] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/agenda/${id}`)
      .then(setExistente)
      .catch((e) => setErro(e.message))
  }, [id])

  if (erro) return <MensagemErro className="m-6">{erro}</MensagemErro>
  if (!existente) return null

  return <AgendaModal existente={existente} onFechar={onFechar} onSalvo={onSalvo} />
}
