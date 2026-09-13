import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { Botao, MensagemErro } from './ui'

const TIPOS_ACEITOS = 'image/jpeg,image/png,image/webp,image/heic,image/heif,application/pdf'
const TAMANHO_MAXIMO = 8 * 1024 * 1024

function formatarTamanho(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * Seção de arquivos (fotos, PDFs) de uma pessoa. Sem `atendimentoId`/
 * `tratamentoId`, mostra os anexos "gerais" da ficha; com um dos dois,
 * mostra só os que foram enviados naquele item específico do histórico.
 */
export function Anexos({ pessoaId, atendimentoId = null, tratamentoId = null, titulo = 'Arquivos' }) {
  const [itens, setItens] = useState(null)
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const inputRef = useRef(null)

  function carregar() {
    api
      .get(`/pessoas/${pessoaId}/anexos`)
      .then((lista) =>
        setItens(
          lista.filter(
            (a) =>
              (a.atendimento_id ?? null) === atendimentoId &&
              (a.tratamento_id ?? null) === tratamentoId,
          ),
        ),
      )
      .catch((e) => setErro(e.message))
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(carregar, [pessoaId, atendimentoId, tratamentoId])

  async function aoEscolherArquivo(evento) {
    const arquivo = evento.target.files?.[0]
    evento.target.value = '' // permite escolher o mesmo arquivo de novo depois
    if (!arquivo) return

    setErro('')
    if (arquivo.size > TAMANHO_MAXIMO) {
      setErro('Arquivo maior que 8 MB — tente uma foto mais leve.')
      return
    }

    const formData = new FormData()
    formData.append('arquivo', arquivo)
    if (atendimentoId) formData.append('atendimento_id', atendimentoId)
    if (tratamentoId) formData.append('tratamento_id', tratamentoId)

    setEnviando(true)
    try {
      await api.postForm(`/pessoas/${pessoaId}/anexos`, formData)
      carregar()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  async function excluir(id) {
    if (!confirm('Excluir este arquivo? Não pode ser desfeito.')) return
    try {
      await api.del(`/anexos/${id}`)
      carregar()
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold tracking-wider text-stone-400 uppercase">
          {titulo}
        </p>
        <Botao
          variante="fantasma"
          pequeno
          onClick={() => inputRef.current?.click()}
          disabled={enviando}
        >
          {enviando ? 'Enviando...' : '+ Adicionar'}
        </Botao>
        <input
          ref={inputRef}
          type="file"
          accept={TIPOS_ACEITOS}
          onChange={aoEscolherArquivo}
          className="hidden"
        />
      </div>

      <MensagemErro className="mt-2">{erro}</MensagemErro>

      {itens && itens.length === 0 && !erro && (
        <p className="mt-2 text-xs text-stone-400">Nenhum arquivo ainda.</p>
      )}

      {itens && itens.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-2">
          {itens.map((a) => (
            <CartaoAnexo key={a.id} anexo={a} aoExcluir={() => excluir(a.id)} />
          ))}
        </ul>
      )}
    </div>
  )
}

function CartaoAnexo({ anexo, aoExcluir }) {
  const [url, setUrl] = useState(null)
  const ehImagem = anexo.tipo_conteudo.startsWith('image/')

  useEffect(() => {
    let ativo = true
    let objectUrl
    api
      .getBlob(`/anexos/${anexo.id}/arquivo`)
      .then((blob) => {
        if (!ativo) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch(() => {})
    return () => {
      ativo = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [anexo.id])

  return (
    <li
      className="group relative h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-stone-100 ring-1 ring-stone-900/10"
      title={`${anexo.nome_arquivo} · ${formatarTamanho(anexo.tamanho_bytes)}${anexo.descricao ? ` · ${anexo.descricao}` : ''}`}
    >
      {ehImagem ? (
        url ? (
          <a href={url} target="_blank" rel="noreferrer">
            <img src={url} alt={anexo.nome_arquivo} className="h-full w-full object-cover" />
          </a>
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-emerald-700" />
          </div>
        )
      ) : (
        <a
          href={url ?? undefined}
          target="_blank"
          rel="noreferrer"
          className="flex h-full w-full flex-col items-center justify-center gap-1 p-1.5 text-center hover:bg-stone-200/60"
        >
          <IconePdf className="h-6 w-6 text-stone-400" />
          <span className="line-clamp-2 text-[9px] leading-tight break-all text-stone-500">
            {anexo.nome_arquivo}
          </span>
        </a>
      )}
      <button
        type="button"
        onClick={aoExcluir}
        aria-label={`Excluir ${anexo.nome_arquivo}`}
        className="absolute top-0.5 right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-stone-900/60 text-xs leading-none text-white opacity-0 transition group-hover:opacity-100 hover:bg-red-600"
      >
        ×
      </button>
    </li>
  )
}

function IconePdf({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M6 2h9l5 5v15H6z" strokeLinejoin="round" />
      <path d="M15 2v5h5" strokeLinejoin="round" />
    </svg>
  )
}
