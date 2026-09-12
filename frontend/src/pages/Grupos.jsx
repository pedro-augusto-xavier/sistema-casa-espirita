import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { GrupoModal } from '../components/GrupoModal'
import {
  Botao,
  Carregando,
  EstadoVazio,
  MensagemErro,
  Paginacao,
  TituloPagina,
} from '../components/ui'
import { isoParaData } from '../utils/formatadores'

export function Grupos() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [pagina, setPagina] = useState(1)
  const [modalAberto, setModalAberto] = useState(false)
  const [editando, setEditando] = useState(null)
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    api
      .get(`/grupos?page=${pagina}&size=20`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [pagina, versao])

  function aoSalvar() {
    setModalAberto(false)
    setEditando(null)
    setVersao((v) => v + 1)
  }

  async function excluir(id, evento) {
    evento.stopPropagation()
    if (!confirm('Excluir esta sessão de grupo?')) return
    try {
      await api.del(`/grupos/${id}`)
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
          titulo="Grupos"
          subtitulo="Grupo Despertar, Grupo de Estudos — presença registrada por sessão."
          acoes={<Botao onClick={() => setModalAberto(true)}>+ Nova sessão</Botao>}
        />

        <MensagemErro className="mt-4">{erro}</MensagemErro>

        <div className="mt-5 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!dados ? (
            <Carregando />
          ) : dados.items.length === 0 ? (
            <EstadoVazio
              titulo="Nenhuma sessão registrada"
              descricao="Registre a primeira sessão de grupo e marque quem esteve presente."
              acao={<Botao onClick={() => setModalAberto(true)}>+ Nova sessão</Botao>}
            />
          ) : (
            <ul className="divide-y divide-stone-100">
              {dados.items.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => setEditando(s.id)}
                    className="group flex w-full items-center gap-4 px-4 py-3 text-left transition hover:bg-emerald-50/50 sm:px-5"
                  >
                    <Data iso={s.data} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-stone-800 group-hover:text-emerald-950">
                        {s.tipo_nome}
                      </p>
                      <p className="truncate text-xs text-stone-500">
                        {s.responsavel?.nome_completo
                          ? `Responsável: ${s.responsavel.nome_completo}`
                          : 'sem responsável definido'}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="font-display text-xl font-semibold text-emerald-900">
                        {s.qtd_presentes}
                      </p>
                      <p className="text-[10px] tracking-wider text-stone-400 uppercase">
                        {s.qtd_presentes === 1 ? 'presente' : 'presentes'}
                      </p>
                    </div>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => excluir(s.id, e)}
                      onKeyDown={(e) => e.key === 'Enter' && excluir(s.id, e)}
                      className="ml-2 rounded-lg px-2 py-1 text-xs text-stone-400 opacity-0 transition group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 focus:opacity-100"
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

      {modalAberto && <GrupoModal onFechar={() => setModalAberto(false)} onSalvo={aoSalvar} />}
      {editando && (
        <DetalheGrupo id={editando} onFechar={() => setEditando(null)} onSalvo={aoSalvar} />
      )}
    </div>
  )
}

/** Quadradinho de data no estilo calendário: dia grande, mês/ano pequeno. */
export function Data({ iso }) {
  const [dia, mes, ano] = (isoParaData(iso) || '--/--/----').split('/')
  return (
    <div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-lg bg-stone-100 ring-1 ring-stone-900/5">
      <span className="font-display text-lg leading-none font-semibold text-emerald-950">
        {dia}
      </span>
      <span className="mt-0.5 text-[10px] leading-none text-stone-500">
        {mes}/{ano.slice(-2)}
      </span>
    </div>
  )
}

function DetalheGrupo({ id, onFechar, onSalvo }) {
  const [existente, setExistente] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/grupos/${id}`)
      .then(setExistente)
      .catch((e) => setErro(e.message))
  }, [id])

  if (erro) return <MensagemErro className="m-6">{erro}</MensagemErro>
  if (!existente) return null

  return <GrupoModal existente={existente} onFechar={onFechar} onSalvo={onSalvo} />
}
