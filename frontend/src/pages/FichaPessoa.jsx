import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { AtendimentoDetalheModal } from '../components/AtendimentoDetalheModal'
import { AtendimentoModal } from '../components/AtendimentoModal'
import { Cabecalho } from '../components/Cabecalho'
import { FichaCaso } from '../components/FichaCaso'
import { TratamentoDetalheModal } from '../components/TratamentoDetalheModal'
import {
  Avatar,
  Botao,
  BotaoLink,
  Carregando,
  EstadoVazio,
  MensagemErro,
  Pill,
} from '../components/ui'
import { useAuth } from '../auth/AuthContext'
import {
  ROTULO_ESTADO_CIVIL,
  ROTULO_PAPEL,
  TOM_PAPEL,
  isoParaData,
  mascaraCpf,
  mascaraTelefone,
  rotuloFilhos,
} from '../utils/formatadores'

const ROTULO_TIPO = {
  atendimento: 'Atendimento',
  tratamento_inicio: 'Início de tratamento',
  evolucao: 'Evolução',
}

const ROTULO_MODALIDADE = {
  presencial: 'Presencial',
  video: 'Vídeo',
  distancia: 'À distância',
}

// cor do ponto na linha do tempo e da etiqueta, por tipo de registro
const ESTILO_TIPO = {
  atendimento: { ponto: 'bg-emerald-600', tom: 'verde' },
  tratamento_inicio: { ponto: 'bg-amber-500', tom: 'ambar' },
  evolucao: { ponto: 'bg-sky-500', tom: 'azul' },
}

export function FichaPessoa() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { usuario } = useAuth()

  const [pessoa, setPessoa] = useState(null)
  const [historico, setHistorico] = useState([])
  const [casos, setCasos] = useState([]) // fichas de acompanhamento (Desobsessão etc.)
  const [edicoes, setEdicoes] = useState([])
  const [mostrarEdicoes, setMostrarEdicoes] = useState(false)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [modalAberto, setModalAberto] = useState(null) // 'atendimento' | null
  const [detalhe, setDetalhe] = useState(null) // { tipo: 'atendimento' | 'tratamento', id }
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    setCarregando(true)
    setErro('')
    Promise.all([
      api.get(`/pessoas/${id}`),
      api.get(`/pessoas/${id}/historico`),
      api
        .get(`/tratamentos?pessoa_id=${id}&size=50`)
        .then((d) => Promise.all(d.items.map((t) => api.get(`/tratamentos/${t.id}`)))),
    ])
      .then(([p, h, c]) => {
        setPessoa(p)
        setHistorico(h)
        // abertas primeiro, depois as concluídas
        setCasos([...c].sort((a, b) => (a.status === b.status ? 0 : a.status === 'concluido' ? 1 : -1)))
        if (p && usuario.papel === 'admin') {
          api
            .get(`/auditoria?entidade=pessoa&entidade_id=${id}&size=50`)
            .then((d) => setEdicoes(d.items))
            .catch(() => {})
        }
      })
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [id, versao, usuario.papel])

  function aoCriarRegistro() {
    setModalAberto(null)
    setVersao((v) => v + 1)
  }

  function abrirDetalhe(item) {
    if (item.tipo === 'atendimento' && item.atendimento_id) {
      setDetalhe({ tipo: 'atendimento', id: item.atendimento_id })
    } else if (item.tratamento_id) {
      setDetalhe({ tipo: 'tratamento', id: item.tratamento_id })
    }
  }

  function fecharDetalhe() {
    setDetalhe(null)
    setVersao((v) => v + 1) // pode ter mudado algo (evolução, assistido concluído)
  }

  async function desativar() {
    if (!confirm(`Desativar a ficha de ${pessoa.nome_completo}?`)) return
    try {
      await api.del(`/pessoas/${id}`)
      navigate('/')
    } catch (e) {
      setErro(e.message)
    }
  }

  async function exportarDados() {
    try {
      const dados = await api.get(`/pessoas/${id}/exportar`)
      const blob = new Blob([JSON.stringify(dados, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ficha-${pessoa.nome_completo.replace(/\s+/g, '_')}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setErro(e.message)
    }
  }

  async function anonimizar() {
    if (
      !confirm(
        `Isso apaga os dados pessoais de ${pessoa.nome_completo} (CPF, telefone, endereço...) e não pode ser desfeito. O histórico de atendimentos é mantido. Continuar?`,
      )
    )
      return
    try {
      await api.post(`/pessoas/${id}/anonimizar`)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  if (carregando) {
    return (
      <div className="min-h-screen bg-stone-100">
        <Cabecalho />
        <Carregando />
      </div>
    )
  }

  if (erro && !pessoa) {
    return (
      <div className="min-h-screen bg-stone-100">
        <Cabecalho />
        <main className="mx-auto max-w-3xl p-6">
          <MensagemErro>{erro}</MensagemErro>
        </main>
      </div>
    )
  }

  // pessoas ligadas por pastas de acompanhamento: de quem esta pessoa é
  // responsável (filhos, pais...) e de quem ela é assistida
  const ligadas = pessoasLigadas(casos, pessoa.id)

  const atendimentos = historico.filter((h) => h.tipo === 'atendimento')
  const ultimoAtendimento = atendimentos[0]?.data // histórico já vem do mais recente
  const pastasAbertas = casos.filter((c) => c.status !== 'concluido').length

  const endereco = [
    pessoa.logradouro,
    pessoa.numero,
    pessoa.bairro,
    pessoa.cidade && pessoa.uf ? `${pessoa.cidade}/${pessoa.uf}` : pessoa.cidade,
  ]
    .filter(Boolean)
    .join(', ')

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-stone-500 transition hover:text-emerald-800"
        >
          ← Voltar para a lista
        </Link>

        {/* ---------- cabeçalho da ficha ---------- */}
        <section className="mt-4 overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-stone-900/5 animate-entrar">
          <div className="h-1.5 bg-linear-to-r from-emerald-800 via-emerald-600 to-amber-500" />
          <div className="p-6 sm:p-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex items-center gap-4">
                <Avatar nome={pessoa.nome_completo} className="h-16 w-16 text-xl" />
                <div>
                  <h1 className="font-display text-2xl font-semibold text-emerald-950 sm:text-3xl">
                    {pessoa.nome_completo}
                  </h1>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {pessoa.papeis.length === 0 && <Pill tom="cinza">sem papel definido</Pill>}
                    {pessoa.papeis.map((p) => (
                      <Pill key={p} tom={TOM_PAPEL[p] ?? 'cinza'}>
                        {ROTULO_PAPEL[p] ?? p}
                      </Pill>
                    ))}
                    {!pessoa.ativo && <Pill tom="cinza">inativa</Pill>}
                    {pessoa.anonimizada && <Pill tom="vermelho">dados anonimizados</Pill>}
                  </div>
                </div>
              </div>

              <div className="flex shrink-0 gap-2">
                <BotaoLink to={`/pessoas/${id}/editar`} variante="secundario">
                  Editar
                </BotaoLink>
                {pessoa.ativo && (
                  <Botao variante="perigo" onClick={desativar}>
                    Desativar
                  </Botao>
                )}
              </div>
            </div>

            {/* números da pessoa: quantas vezes veio, quando foi a última, pastas abertas */}
            <div className="mt-6 grid grid-cols-3 divide-x divide-stone-100 rounded-xl bg-stone-50 ring-1 ring-stone-900/5">
              <Numero valor={atendimentos.length} rotulo={atendimentos.length === 1 ? 'atendimento' : 'atendimentos'} />
              <Numero valor={ultimoAtendimento ? isoParaData(ultimoAtendimento) : '—'} rotulo="último atendimento" pequeno />
              <Numero valor={pastasAbertas} rotulo={pastasAbertas === 1 ? 'tratamento aberto' : 'tratamentos abertos'} />
            </div>

            <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
              <Item label="Nascimento" valor={isoParaData(pessoa.data_nascimento)} />
              <Item label="Telefone" valor={pessoa.telefone && mascaraTelefone(pessoa.telefone)} />
              <Item label="CPF" valor={pessoa.cpf && mascaraCpf(pessoa.cpf)} />
              <Item label="Estado civil" valor={ROTULO_ESTADO_CIVIL[pessoa.estado_civil]} />
              <Item label="Filhos" valor={rotuloFilhos(pessoa.quantidade_filhos)} />
              <Item label="Endereço" valor={endereco} className="col-span-2" />
              <Item label="CEP" valor={pessoa.cep} />
              <Item label="Como conheceu a casa" valor={pessoa.como_conheceu} className="col-span-2 sm:col-span-3" />
            </dl>

            {pessoa.observacoes_gerais && (
              <div className="mt-6 rounded-xl border-l-4 border-amber-400 bg-amber-50/60 p-4">
                <p className="text-[11px] font-semibold tracking-wider text-amber-800 uppercase">
                  Observações
                </p>
                <p className="mt-1 text-sm leading-relaxed text-stone-700">
                  {pessoa.observacoes_gerais}
                </p>
              </div>
            )}

            <MensagemErro className="mt-4">{erro}</MensagemErro>

            {/* ---------- rodapé: PDF e LGPD ---------- */}
            <div className="mt-6 flex flex-wrap items-center gap-1 border-t border-stone-100 pt-4">
              <Botao
                variante="fantasma"
                pequeno
                onClick={async () => {
                  const { gerarPdfFicha } = await import('../utils/gerarPdfFicha')
                  gerarPdfFicha(pessoa, historico)
                }}
              >
                ⬇ Baixar PDF da ficha
              </Botao>
              <span className="mx-2 hidden h-4 w-px bg-stone-200 sm:block" />
              <span className="px-1 text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
                LGPD
              </span>
              <Botao variante="fantasma" pequeno onClick={exportarDados}>
                Exportar dados (JSON)
              </Botao>
              {usuario.papel === 'admin' && !pessoa.anonimizada && (
                <Botao
                  variante="fantasma"
                  pequeno
                  onClick={anonimizar}
                  className="text-red-600 hover:bg-red-50 hover:text-red-700"
                >
                  Anonimizar
                </Botao>
              )}
              {usuario.papel === 'admin' && edicoes.length > 0 && (
                <Botao variante="fantasma" pequeno onClick={() => setMostrarEdicoes((v) => !v)}>
                  {mostrarEdicoes ? 'Ocultar edições' : 'Quem editou esta ficha'}
                </Botao>
              )}
            </div>

            {mostrarEdicoes && (
              <ul className="mt-3 flex flex-col gap-2 rounded-xl bg-stone-50 p-4 text-xs text-stone-500 animate-surgir">
                {edicoes.map((e) => (
                  <li key={e.id}>
                    <span className="font-medium text-stone-700">{e.usuario_nome || 'sistema'}</span>{' '}
                    {e.acao === 'criar' ? 'criou a ficha' : 'alterou a ficha'} em{' '}
                    {new Date(e.criado_em).toLocaleString('pt-BR')}
                    {e.dados && Object.keys(e.dados).length > 0 && (
                      <ul className="mt-0.5 ml-4 list-disc text-stone-400">
                        {Object.entries(e.dados).map(([campo, valor]) => (
                          <li key={campo}>{formatarAlteracao(campo, valor)}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* ---------- pessoas ligadas (a família da pasta) ---------- */}
        {(ligadas.responsavelDe.length > 0 || ligadas.assistidoDe.length > 0) && (
          <section className="mt-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-stone-900/5 animate-entrar">
            <h2 className="font-display text-xl font-semibold text-emerald-950">Pessoas ligadas</h2>
            <p className="mt-0.5 text-xs text-stone-400">
              Cada uma tem a própria ficha — clique pra abrir.
            </p>
            <div className="mt-4 flex flex-col gap-4">
              {ligadas.responsavelDe.length > 0 && (
                <GrupoLigadas
                  titulo={`${pessoa.nome_completo.split(' ')[0]} é responsável por`}
                  pessoas={ligadas.responsavelDe}
                />
              )}
              {ligadas.assistidoDe.length > 0 && (
                <GrupoLigadas
                  titulo={`${pessoa.nome_completo.split(' ')[0]} é assistida(o) de`}
                  pessoas={ligadas.assistidoDe}
                />
              )}
            </div>
          </section>
        )}

        {/* ---------- fichas de acompanhamento (Desobsessão etc.) ---------- */}
        {casos.length > 0 && (
          <section className="mt-6 flex flex-col gap-4 animate-entrar">
            {casos.map((c) => (
              <FichaCaso
                key={c.id}
                caso={c}
                pessoaId={pessoa.id}
                aoMudar={() => setVersao((v) => v + 1)}
                aoAbrir={() => setDetalhe({ tipo: 'tratamento', id: c.id })}
              />
            ))}
          </section>
        )}

        {/* ---------- histórico ---------- */}
        <section className="mt-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-stone-900/5 sm:p-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-baseline gap-3">
              <h2 className="font-display text-2xl font-semibold text-emerald-950">Histórico</h2>
              {historico.length > 0 && (
                <span className="text-sm text-stone-400">
                  {historico.length} {historico.length === 1 ? 'registro' : 'registros'}
                </span>
              )}
            </div>
            <Botao onClick={() => setModalAberto('atendimento')}>+ Registrar atendimento</Botao>
          </div>

          {historico.length === 0 ? (
            <EstadoVazio
              titulo="Nenhum atendimento ainda"
              descricao="Cada visita vai aparecer aqui, da mais recente à mais antiga. Clique num registro para abrir, editar ou baixar o PDF."
              acao={
                <Botao onClick={() => setModalAberto('atendimento')}>+ Registrar atendimento</Botao>
              }
            />
          ) : (
            <>
              <p className="mt-1 text-xs text-stone-400">
                Clique num registro para abrir, editar ou baixar o PDF.
              </p>
              <ol className="relative mt-5 ml-2.5 border-l-2 border-stone-200 pl-7">
                {/* as anotações do diário já aparecem na ficha de acompanhamento */}
                {historico.filter((item) => item.tipo !== 'evolucao').map((item, i) => (
                  <LinhaHistorico
                    key={i}
                    item={item}
                    aoAbrir={
                      item.atendimento_id || item.tratamento_id ? () => abrirDetalhe(item) : null
                    }
                  />
                ))}
              </ol>
            </>
          )}
        </section>
      </main>

      {modalAberto === 'atendimento' && (
        <AtendimentoModal
          pessoa={pessoa}
          onFechar={() => setModalAberto(null)}
          onSalvo={aoCriarRegistro}
        />
      )}

      {detalhe?.tipo === 'atendimento' && (
        <AtendimentoDetalheModal atendimentoId={detalhe.id} onFechar={fecharDetalhe} />
      )}
      {detalhe?.tipo === 'tratamento' && (
        <TratamentoDetalheModal tratamentoId={detalhe.id} onFechar={fecharDetalhe} />
      )}
    </div>
  )
}

function formatarValor(v) {
  if (v === null || v === undefined || v === '') return '(vazio)'
  if (Array.isArray(v)) return v.join(', ') || '(vazio)'
  return String(v)
}

/** "campo: de → para" quando dá pra comparar; senão só mostra o valor. */
function formatarAlteracao(campo, valor) {
  if (valor && typeof valor === 'object' && 'de' in valor && 'para' in valor) {
    return `${campo}: ${formatarValor(valor.de)} → ${formatarValor(valor.para)}`
  }
  return `${campo}: ${formatarValor(valor)}`
}

/** Junta, de todas as pastas, quem esta pessoa acompanha e quem acompanha ela.
 * Cada pessoa aparece uma vez, com as pastas (tipos) que a ligam. */
function pessoasLigadas(casos, meuId) {
  const responsavelDe = new Map()
  const assistidoDe = new Map()

  function junta(mapa, p, caso) {
    if (!p || p.id === meuId) return
    const atual = mapa.get(p.id) ?? { pessoa: p, pastas: [], concluida: true }
    atual.pastas.push(caso.tipo_nome)
    if (caso.status !== 'concluido') atual.concluida = false
    mapa.set(p.id, atual)
  }

  for (const caso of casos) {
    if (caso.solicitante?.id === meuId) {
      for (const a of caso.assistidos) junta(responsavelDe, a.pessoa, caso)
    } else if (caso.assistidos.some((a) => a.pessoa.id === meuId)) {
      junta(assistidoDe, caso.solicitante, caso)
    }
  }
  return {
    responsavelDe: [...responsavelDe.values()],
    assistidoDe: [...assistidoDe.values()],
  }
}

function GrupoLigadas({ titulo, pessoas }) {
  return (
    <div>
      <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">{titulo}</p>
      <ul className="mt-2 flex flex-wrap gap-2">
        {pessoas.map(({ pessoa: p, pastas, concluida }) => (
          <li key={p.id}>
            <Link
              to={`/pessoas/${p.id}`}
              className={`group flex items-center gap-2.5 rounded-xl bg-stone-50 py-2 pr-4 pl-2 ring-1 ring-stone-900/5 transition hover:bg-emerald-50 hover:ring-emerald-600/30 ${
                concluida ? 'opacity-60' : ''
              }`}
            >
              <Avatar nome={p.nome_completo} className="h-9 w-9 text-xs" />
              <span className="leading-tight">
                <span className="block text-sm font-medium text-stone-800 group-hover:text-emerald-950">
                  {p.nome_completo}
                </span>
                <span className="block text-[11px] text-stone-400">
                  {[...new Set(pastas)].join(' · ')}
                  {concluida ? ' · concluída' : ''}
                </span>
              </span>
              <span className="ml-1 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-emerald-700">
                →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Numero({ valor, rotulo, pequeno = false }) {
  return (
    <div className="px-4 py-3 text-center">
      <p
        className={`font-display font-semibold text-emerald-950 ${pequeno ? 'text-lg leading-8' : 'text-2xl'}`}
      >
        {valor}
      </p>
      <p className="text-[10px] tracking-wider text-stone-400 uppercase">{rotulo}</p>
    </div>
  )
}

function Item({ label, valor, className = '' }) {
  return (
    <div className={className}>
      <dt className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">{label}</dt>
      <dd className="mt-0.5 text-sm text-stone-800">{valor || <span className="text-stone-300">—</span>}</dd>
    </div>
  )
}

/** Um registro da linha do tempo, no estilo da ficha de papel: data em
 * destaque, a observação em evidência e o card inteiro clicável. */
function LinhaHistorico({ item, aoAbrir }) {
  const d = item.detalhes ?? {}
  const estilo = ESTILO_TIPO[item.tipo] ?? { ponto: 'bg-stone-400', tom: 'cinza' }
  const Envoltorio = aoAbrir ? 'button' : 'div'

  return (
    <li className="relative pb-6 last:pb-0">
      <span
        className={`absolute top-3 -left-9.75 flex h-5 w-5 items-center justify-center rounded-full ring-4 ring-white ${estilo.ponto}`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-white" />
      </span>

      <Envoltorio
        type={aoAbrir ? 'button' : undefined}
        onClick={aoAbrir ?? undefined}
        className={`group block w-full rounded-xl bg-stone-50/70 p-4 text-left ring-1 ring-stone-900/5 transition ${
          aoAbrir
            ? 'cursor-pointer hover:bg-white hover:shadow-md hover:ring-emerald-600/30 focus-visible:ring-2 focus-visible:ring-emerald-500/40 focus-visible:outline-none'
            : ''
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-display text-lg font-semibold text-emerald-950">
              {isoParaData(item.data)}
            </span>
            <Pill tom={estilo.tom}>{ROTULO_TIPO[item.tipo] ?? item.tipo}</Pill>
          </div>
          {aoAbrir && (
            <span className="text-xs text-stone-400 transition group-hover:text-emerald-800">
              abrir →
            </span>
          )}
        </div>

        <div className="mt-2 flex flex-col gap-1 text-sm text-stone-600">
          {item.tipo === 'atendimento' && (
            <>
              <p>
                {ROTULO_MODALIDADE[d.modalidade] ?? d.modalidade}
                {d.presente === false && (
                  <span className="text-stone-400"> · não esteve presente</span>
                )}
              </p>
              {d.atendido_por && (
                <p>
                  <Rotulo>Atendido por</Rotulo> {d.atendido_por}
                </p>
              )}
              {d.solicitante && (
                <p>
                  <Rotulo>Solicitante</Rotulo> {d.solicitante}
                </p>
              )}
              {d.tratamentos?.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {d.tratamentos.map((t, i) => (
                    <Pill key={i} tom="verde">
                      {t.nome}
                      {t.sessoes_previstas ? ` · ${t.sessoes_previstas}x` : ''}
                    </Pill>
                  ))}
                </div>
              )}
              {d.observacao && <Citacao>{d.observacao}</Citacao>}
            </>
          )}

          {item.tipo === 'tratamento_inicio' && (
            <>
              <p className="font-medium text-stone-800">{d.tipo_nome}</p>
              {d.solicitante && (
                <p>
                  <Rotulo>Responsável</Rotulo> {d.solicitante}
                </p>
              )}
              {d.sessoes_previstas != null && <p>{d.sessoes_previstas} sessões previstas</p>}
              {d.observacao && <Citacao>{d.observacao}</Citacao>}
            </>
          )}

          {item.tipo === 'evolucao' && (
            <>
              <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
                {d.tipo_nome}
              </p>
              <Citacao>
                {d.texto}
                {d.registrado_por && (
                  <span className="text-stone-400 not-italic"> — {d.registrado_por}</span>
                )}
              </Citacao>
            </>
          )}

        </div>
      </Envoltorio>
    </li>
  )
}

function Rotulo({ children }) {
  return <span className="text-stone-400">{children}:</span>
}

/** A observação é o que mais importa ler na ficha: caixa âmbar, texto maior. */
function Citacao({ children }) {
  return (
    <div className="mt-2 rounded-lg border-l-4 border-amber-400 bg-amber-50/70 px-3 py-2">
      <p className="text-[15px] leading-relaxed whitespace-pre-line text-stone-800">{children}</p>
    </div>
  )
}
