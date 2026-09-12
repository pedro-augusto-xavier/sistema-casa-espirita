import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { PessoaForm } from '../components/PessoaForm'
import { Carregando, MensagemErro, TituloPagina } from '../components/ui'
import { isoParaData, mascaraCpf, mascaraTelefone } from '../utils/formatadores'

export function EditarPessoa() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [valores, setValores] = useState(null)
  const [papeis, setPapeis] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api
      .get(`/pessoas/${id}`)
      .then((p) => {
        setValores({
          nome_completo: p.nome_completo,
          data_nascimento: isoParaData(p.data_nascimento) || '',
          sexo: p.sexo,
          cpf: p.cpf ? mascaraCpf(p.cpf) : '',
          telefone: p.telefone ? mascaraTelefone(p.telefone) : '',
          logradouro: p.logradouro || '',
          numero: p.numero || '',
          complemento: p.complemento || '',
          bairro: p.bairro || '',
          cidade: p.cidade || '',
          uf: p.uf || '',
          cep: p.cep || '',
          como_conheceu: p.como_conheceu || '',
          observacoes_gerais: p.observacoes_gerais || '',
        })
        setPapeis({
          trabalhador: p.papeis.includes('trabalhador'),
          assistido: p.papeis.includes('assistido'),
        })
      })
      .catch((e) => setErro(e.message))
  }, [id])

  async function salvar(corpo) {
    await api.patch(`/pessoas/${id}`, corpo)
    navigate(`/pessoas/${id}`)
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        <Link
          to={`/pessoas/${id}`}
          className="inline-flex items-center gap-1 text-sm text-stone-500 transition hover:text-emerald-800"
        >
          ← Voltar para a ficha
        </Link>

        <div className="mt-4">
          <TituloPagina
            titulo="Editar pessoa"
            subtitulo={valores ? valores.nome_completo : null}
          />
        </div>

        <div className="mt-6">
          <MensagemErro>{erro}</MensagemErro>
          {!erro && !valores && <Carregando />}
          {valores && papeis && (
            <div className="animate-entrar">
              <PessoaForm
                valoresIniciais={valores}
                papeisIniciais={papeis}
                aoSalvar={salvar}
                linkCancelar={`/pessoas/${id}`}
                textoBotao="Salvar alterações"
              />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
