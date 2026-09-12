import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, isoParaData, mascaraData } from '../utils/formatadores'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'
import { Avatar, Botao, Campo, MensagemErro } from './ui'

function hoje() {
  const d = new Date()
  return mascaraData(
    `${String(d.getDate()).padStart(2, '0')}${String(d.getMonth() + 1).padStart(2, '0')}${d.getFullYear()}`,
  )
}

/** Cria um atendimento novo (passe `pessoa`) ou edita um existente (passe `existente`). */
export function AtendimentoModal({ pessoa, existente, onFechar, onSalvo }) {
  const editando = Boolean(existente)
  const pessoaAtual = pessoa ?? existente?.pessoa

  const [tipos, setTipos] = useState([])
  const [data, setData] = useState(existente ? isoParaData(existente.data) : hoje())
  const [atendidoPor, setAtendidoPor] = useState(existente?.atendido_por ?? null)
  const [modalidade, setModalidade] = useState(existente?.modalidade ?? 'presencial')
  const [presente, setPresente] = useState(existente?.presente ?? true)
  const [solicitante, setSolicitante] = useState(existente?.solicitante ?? null)
  const [tratamentosMarcados, setTratamentosMarcados] = useState(
    existente ? existente.tratamentos.map((t) => t.tipo_tratamento_id) : [],
  )
  // "nº de vezes" por tipo de tratamento (só faz sentido pros de formato "caso")
  const [vezesPorTipo, setVezesPorTipo] = useState(() =>
    Object.fromEntries(
      (existente?.tratamentos ?? []).map((t) => [t.tipo_tratamento_id, t.sessoes_previstas ?? '']),
    ),
  )
  // assistidos por tipo "caso": por quem a pessoa pediu (começa com ela mesma)
  const [assistidosPorTipo, setAssistidosPorTipo] = useState({})
  const [fichasAbertas, setFichasAbertas] = useState([])
  const [observacao, setObservacao] = useState(existente?.observacao ?? '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const idPessoa = pessoaAtual?.id

  useEffect(() => {
    // tudo que pode ser marcado num atendimento individual (fica de fora só os grupos)
    api
      .get('/tipos-tratamento')
      .then((lista) => setTipos(lista.filter((t) => t.formato !== 'grupo')))
      .catch((e) => setErro(e.message))
  }, [])

  useEffect(() => {
    // fichas de acompanhamento (Desobsessão etc.) que a pessoa já tem abertas
    if (!idPessoa) return
    api
      .get(`/tratamentos?pessoa_id=${idPessoa}&status=em_andamento&size=50`)
      .then((d) => setFichasAbertas(d.items))
      .catch(() => setFichasAbertas([]))
  }, [idPessoa])

  function alternarTratamento(id) {
    setTratamentosMarcados((atual) =>
      atual.includes(id) ? atual.filter((t) => t !== id) : [...atual, id],
    )
  }

  const casosMarcados = tipos.filter(
    (t) => t.formato === 'caso' && tratamentosMarcados.includes(t.id),
  )

  function assistidosDe(tipoId) {
    return assistidosPorTipo[tipoId] ?? (pessoaAtual ? [pessoaAtual] : [])
  }

  function alternarAssistido(tipoId, p) {
    if (!p) return
    setAssistidosPorTipo((atual) => {
      const lista = assistidosDe(tipoId)
      const tem = lista.some((x) => x.id === p.id)
      return { ...atual, [tipoId]: tem ? lista.filter((x) => x.id !== p.id) : [...lista, p] }
    })
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    const dataIso = dataParaIso(data)
    if (!dataIso) {
      setErro('Data inválida — use o formato dd/mm/aaaa.')
      return
    }

    const corpo = {
      data: dataIso,
      atendido_por_id: atendidoPor?.id ?? null,
      modalidade,
      presente,
      solicitante_id: solicitante?.id ?? null,
      observacao: observacao || null,
      tratamentos: tratamentosMarcados.map((id) => ({
        tipo_tratamento_id: id,
        sessoes_previstas: vezesPorTipo[id] ? Number(vezesPorTipo[id]) : null,
        assistidos: assistidosDe(id).map((p) => p.id),
      })),
    }

    setEnviando(true)
    try {
      if (editando) {
        await api.patch(`/atendimentos/${existente.id}`, corpo)
      } else {
        await api.post('/atendimentos', { ...corpo, pessoa_id: idPessoa })
      }
      onSalvo()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={editando ? 'Editar atendimento' : 'Registrar atendimento'} onFechar={onFechar}>
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Campo label="Data">
            <input
              inputMode="numeric"
              placeholder="dd/mm/aaaa"
              maxLength={10}
              value={data}
              onChange={(e) => setData(mascaraData(e.target.value))}
              className="campo"
            />
          </Campo>
          <Campo label="Modalidade">
            <select
              value={modalidade}
              onChange={(e) => setModalidade(e.target.value)}
              className="campo"
            >
              <option value="presencial">Presencial</option>
              <option value="video">Vídeo</option>
              <option value="distancia">À distância</option>
            </select>
          </Campo>
        </div>

        <Campo label="Atendido por" dica="médium / trabalhador">
          <SeletorPessoa
            valor={atendidoPor}
            aoSelecionar={setAtendidoPor}
            papel="trabalhador"
            placeholder="Buscar trabalhador..."
          />
        </Campo>

        <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-700 select-none hover:bg-stone-50">
          <input
            type="checkbox"
            checked={presente}
            onChange={(e) => setPresente(e.target.checked)}
            className="accent-emerald-700"
          />
          A pessoa esteve presente
        </label>

        {!presente && (
          <div className="animate-surgir">
            <Campo label="Quem veio no lugar dela" dica="ex: o pai registrando pelo filho">
              <SeletorPessoa
                valor={solicitante}
                aoSelecionar={setSolicitante}
                placeholder="Buscar pessoa..."
              />
            </Campo>
          </div>
        )}

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-stone-700">Tratamentos do dia</legend>
          <div className="flex flex-wrap gap-1.5">
            {tipos.map((t) => {
              const marcado = tratamentosMarcados.includes(t.id)
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => alternarTratamento(t.id)}
                  aria-pressed={marcado}
                  className={`rounded-full px-3 py-1 text-sm transition ${
                    marcado
                      ? 'bg-emerald-800 font-medium text-white shadow-sm'
                      : 'bg-white text-stone-600 ring-1 ring-stone-900/10 hover:bg-stone-50'
                  }`}
                >
                  {marcado ? '✓ ' : ''}
                  {t.nome}
                </button>
              )
            })}
          </div>
        </fieldset>

        {/* tratamentos de "caso" (Desobsessão) têm pasta própria: a capa tem
            Responsável (quem vem à casa) e Assistidos (por quem ela pediu) */}
        {casosMarcados.map((t) => {
          const aberta = fichasAbertas.find((f) => f.tipo_tratamento_id === t.id)
          const assistidos = assistidosDe(t.id)
          const euMesmo = pessoaAtual && assistidos.some((p) => p.id === pessoaAtual.id)
          return (
            <div
              key={t.id}
              className="rounded-xl border-l-4 border-amber-400 bg-amber-50/60 p-4 animate-surgir"
            >
              <p className="text-[11px] font-semibold tracking-wider text-amber-800 uppercase">
                Pasta de {t.nome}
              </p>

              {aberta ? (
                <p className="mt-1 text-sm text-stone-700">
                  Pasta aberta desde <strong>{isoParaData(aberta.data_inicio)}</strong>
                  {aberta.sessoes_previstas
                    ? ` — ${aberta.sessoes_realizadas} de ${aberta.sessoes_previstas} vezes feitas`
                    : ''}
                  . Este atendimento conta como mais uma vez.
                </p>
              ) : (
                <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto]">
                  <p className="text-sm text-stone-700">
                    <span className="text-stone-500">Responsável:</span>{' '}
                    <strong>{pessoaAtual?.nome_completo}</strong>
                  </p>
                  <label className="flex items-center gap-2 text-sm font-medium text-stone-700">
                    Nº de vezes
                    <input
                      type="number"
                      min="1"
                      placeholder="ex: 3"
                      value={vezesPorTipo[t.id] ?? ''}
                      onChange={(e) =>
                        setVezesPorTipo((v) => ({ ...v, [t.id]: e.target.value }))
                      }
                      className="campo w-20"
                    />
                  </label>
                </div>
              )}

              <div className="mt-3">
                <p className="text-sm font-medium text-stone-700">
                  {aberta ? 'Incluir assistidos' : 'Assistidos'}
                  <span className="ml-1.5 text-xs font-normal text-stone-500">
                    por quem {pessoaAtual ? 'ela' : 'a pessoa'} pediu — filhos, amigos, ela mesma
                  </span>
                </p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  {pessoaAtual && (
                    <button
                      type="button"
                      onClick={() => alternarAssistido(t.id, pessoaAtual)}
                      aria-pressed={euMesmo}
                      className={`rounded-full px-3 py-1 text-xs transition ${
                        euMesmo
                          ? 'bg-emerald-800 font-medium text-white'
                          : 'bg-white text-stone-600 ring-1 ring-stone-900/10 hover:bg-stone-50'
                      }`}
                    >
                      {euMesmo ? '✓ ' : ''}ela mesma
                    </button>
                  )}
                  {assistidos
                    .filter((p) => p.id !== pessoaAtual?.id)
                    .map((p) => (
                      <span
                        key={p.id}
                        className="flex items-center gap-1.5 rounded-full bg-white py-0.5 pr-1 pl-0.5 text-xs text-emerald-950 ring-1 ring-emerald-800/15"
                      >
                        <Avatar nome={p.nome_completo} className="h-5 w-5 text-[8px]" />
                        {p.nome_completo}
                        <button
                          type="button"
                          onClick={() => alternarAssistido(t.id, p)}
                          aria-label={`Remover ${p.nome_completo}`}
                          className="flex h-4 w-4 items-center justify-center rounded-full text-stone-400 hover:bg-stone-100 hover:text-red-600"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                </div>
                <div className="mt-2">
                  <SeletorPessoa
                    valor={null}
                    aoSelecionar={(p) => alternarAssistido(t.id, p)}
                    placeholder="Adicionar assistido (filho, pai, amigo...)"
                    permitirCadastro
                  />
                </div>
              </div>
            </div>
          )
        })}

        <Campo label="Observação">
          <textarea
            rows={3}
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
            className="campo"
            placeholder="O que foi conversado, orientações, encaminhamentos..."
          />
        </Campo>

        <MensagemErro>{erro}</MensagemErro>

        <div className="flex justify-end gap-2 pt-1">
          <Botao variante="secundario" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Registrar'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
