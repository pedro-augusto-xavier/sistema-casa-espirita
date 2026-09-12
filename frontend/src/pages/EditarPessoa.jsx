import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { PessoaForm } from '../components/PessoaForm'
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
      <header className="bg-white px-6 py-4 shadow-sm ring-1 ring-stone-900/5">
        <Link to={`/pessoas/${id}`} className="text-sm text-stone-500 hover:underline">
          ← Voltar para a ficha
        </Link>
        <h1 className="font-display text-xl font-semibold text-emerald-900">Editar pessoa</h1>
      </header>

      <main className="mx-auto max-w-2xl p-6">
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        {!erro && !valores && <p className="text-sm text-stone-500">Carregando...</p>}
        {valores && papeis && (
          <PessoaForm
            valoresIniciais={valores}
            papeisIniciais={papeis}
            aoSalvar={salvar}
            linkCancelar={`/pessoas/${id}`}
            textoBotao="Salvar alterações"
          />
        )}
      </main>
    </div>
  )
}
