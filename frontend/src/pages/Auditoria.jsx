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
  login: 'Login',
}

const TOM_ACAO = {
  criar: 'verde',
  atualizar: 'ambar',
  excluir: 'vermelho',
  login: 'cinza',
}

const ROTULO_ENTIDADE = {
  pessoa: 'pessoa',
  atendimento: 'atendimento',
  tratamento: 'tratamento',
  usuario: 'usuário',
  grupo: 'grupo',
  agenda: 'evento',
}

export function Auditoria() {
  const [entidade, setEntidade] = useState('')
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [aberto, setAberto] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams({ page: pagina, size: 30 })
    if (entidade) params.set('entidade', entidade)
    api
      .get(`/auditoria?${params}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [entidade, pagina])

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        <TituloPagina
          titulo="Auditoria"
          subtitulo="Registro de quem criou, alterou ou excluiu cada coisa no sistema."
          acoes={
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
              <option value="usuario">Usuário</option>
            </select>
          }
        />

        <MensagemErro className="mt-4">{erro}</MensagemErro>

        <div className="mt-5 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-stone-900/5">
          {!dados ? (
            <Carregando />
          ) : dados.items.length === 0 ? (
            <EstadoVazio
              titulo="Nada registrado ainda"
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
                        {log.usuario_nome || 'sistema'}
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
