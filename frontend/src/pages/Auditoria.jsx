import { useEffect, useState } from 'react'
import { api } from '../api/client'
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

const ROTULO_ACAO = {
  criar: 'Criou',
  atualizar: 'Atualizou',
  excluir: 'Excluiu',
  login: 'Entrou',
  login_falha: 'Login falhou',
  logout: 'Saiu',
  visualizar: 'Viu dado completo',
  exportar: 'Exportou',
}

const TOM_ACAO = {
  criar: 'verde',
  atualizar: 'ambar',
  excluir: 'vermelho',
  login: 'cinza',
  login_falha: 'vermelho',
  logout: 'cinza',
  visualizar: 'azul',
  exportar: 'azul',
}

const ROTULO_ENTIDADE = {
  pessoa: 'pessoa',
  atendimento: 'atendimento',
  tratamento: 'tratamento',
  usuario: 'usuário',
  anexo: 'arquivo',
  evento_agenda: 'evento',
}

export function Auditoria() {
  const [entidade, setEntidade] = useState('')
  const [acao, setAcao] = useState('')
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [alertas, setAlertas] = useState(null)
  const [erro, setErro] = useState('')
  const [aberto, setAberto] = useState(null)

  useEffect(() => {
    api
      .get('/auditoria/alertas')
      .then(setAlertas)
      .catch(() => {})
  }, [])

  useEffect(() => {
    const params = new URLSearchParams({ page: pagina, size: 30 })
    if (entidade) params.set('entidade', entidade)
    if (acao) params.set('acao', acao)
    api
      .get(`/auditoria?${params}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [entidade, acao, pagina])

  function filtrarAcao(valor) {
    setPagina(1)
    setAcao(valor)
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <TituloPagina
          titulo="Auditoria"
          subtitulo="Quem entrou, criou, alterou, viu ou exportou cada coisa — com data, hora e IP."
          acoes={
            <div className="flex flex-wrap gap-2">
              <select
                value={acao}
                onChange={(e) => filtrarAcao(e.target.value)}
                className="campo w-auto"
              >
                <option value="">Todas as ações</option>
                {Object.entries(ROTULO_ACAO).map(([valor, rotulo]) => (
                  <option key={valor} value={valor}>
                    {rotulo}
                  </option>
                ))}
              </select>
              <select
                value={entidade}
                onChange={(e) => {
                  setPagina(1)
                  setEntidade(e.target.value)
                }}
                className="campo w-auto"
              >
                <option value="">Todas as entidades</option>
                <option value="pessoa">Pessoa</option>
                <option value="atendimento">Atendimento</option>
                <option value="tratamento">Tratamento</option>
                <option value="anexo">Arquivo</option>
                <option value="usuario">Usuário</option>
              </select>
            </div>
          }
        />

        {alertas && (
          <section
            className={`mt-5 rounded-xl p-4 ring-1 ${
              alertas.alerta
                ? 'bg-red-50 ring-red-800/15'
                : 'bg-white ring-stone-900/5'
            }`}
          >
            <p
              className={`text-sm font-medium ${alertas.alerta ? 'text-red-800' : 'text-stone-700'}`}
            >
              {alertas.alerta
                ? 'Atenção: tem movimento fora do comum. Confira abaixo.'
                : 'Nada fora do comum.'}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Indicador
                valor={alertas.falhas_login_24h}
                rotulo="logins que falharam (24h)"
                destaque={alertas.falhas_login_24h >= 10}
                aoClicar={() => filtrarAcao('login_falha')}
              />
              <Indicador
                valor={alertas.acessos_fora_de_hora_7d}
                rotulo="acessos entre 23h e 6h (7 dias)"
                destaque={alertas.acessos_fora_de_hora_7d > 0}
                aoClicar={() => filtrarAcao('login')}
              />
              <Indicador
                valor={alertas.exportacoes_7d}
                rotulo="PDFs/exportações (7 dias)"
                aoClicar={() => filtrarAcao('exportar')}
              />
              <Indicador
                valor={alertas.cpfs_vistos_7d}
                rotulo="CPFs vistos por completo (7 dias)"
                aoClicar={() => filtrarAcao('visualizar')}
              />
            </div>
          </section>
        )}

        <MensagemErro className="mt-4">{erro}</MensagemErro>

        <div className="mt-5 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!dados ? (
            <Carregando />
          ) : dados.items.length === 0 ? (
            <EstadoVazio
              titulo="Nada registrado"
              descricao="Toda ação feita no sistema aparece aqui automaticamente."
            />
          ) : (
            <ul className="divide-y divide-stone-100">
              {dados.items.map((log) => {
                const expandido = aberto === log.id
                const quando = new Date(log.criado_em)
                return (
                  <li key={log.id} className="px-4 py-3 sm:px-5">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                      <span className="w-32 shrink-0 text-xs tabular-nums text-stone-400">
                        {quando.toLocaleDateString('pt-BR')}{' '}
                        <span className="text-stone-300">·</span>{' '}
                        {quando.toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      <span className="font-medium text-stone-800">
                        {log.usuario_nome || (log.acao === 'login_falha' ? '(desconhecido)' : 'sistema')}
                      </span>
                      <Pill tom={TOM_ACAO[log.acao] ?? 'cinza'}>
                        {ROTULO_ACAO[log.acao] ?? log.acao}
                      </Pill>
                      <span className="text-stone-600">
                        {ROTULO_ENTIDADE[log.entidade] ?? log.entidade}
                        {log.entidade_id ? (
                          <span className="text-stone-400"> #{log.entidade_id}</span>
                        ) : null}
                      </span>
                      {log.ip && (
                        <span className="text-xs text-stone-400 tabular-nums">IP {log.ip}</span>
                      )}
                      {log.dados && (
                        <Botao
                          variante="fantasma"
                          pequeno
                          className="ml-auto"
                          onClick={() => setAberto(expandido ? null : log.id)}
                        >
                          {expandido ? 'Ocultar' : 'Detalhes'}
                        </Botao>
                      )}
                    </div>
                    {expandido && (
                      <pre className="mt-2 overflow-x-auto rounded-lg bg-stone-900 p-3 text-xs leading-relaxed text-stone-100 animate-surgir">
                        {JSON.stringify(log.dados, null, 2)}
                      </pre>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        {dados && <Paginacao pagina={pagina} totalPaginas={dados.pages} aoMudar={setPagina} />}
      </main>
    </div>
  )
}

function Indicador({ valor, rotulo, destaque = false, aoClicar }) {
  return (
    <button
      type="button"
      onClick={aoClicar}
      className="rounded-lg bg-white/70 px-3 py-2 text-left ring-1 ring-stone-900/5 transition hover:ring-emerald-600/30"
    >
      <p
        className={`font-display text-2xl font-semibold ${destaque ? 'text-red-700' : 'text-emerald-950'}`}
      >
        {valor}
      </p>
      <p className="text-[11px] leading-tight text-stone-500">{rotulo}</p>
    </button>
  )
}
