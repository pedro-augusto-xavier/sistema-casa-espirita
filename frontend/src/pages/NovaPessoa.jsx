import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const VAZIO = {
  nome_completo: '',
  data_nascimento: '',
  sexo: 'nao_informado',
  cpf: '',
  telefone: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  cep: '',
  como_conheceu: '',
  observacoes_gerais: '',
  consentimento_lgpd: false,
}

export function NovaPessoa() {
  const navigate = useNavigate()
  const [form, setForm] = useState(VAZIO)
  const [papeis, setPapeis] = useState({ trabalhador: false, assistido: true })
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  function campo(nome) {
    return {
      value: form[nome],
      onChange: (e) => setForm((f) => ({ ...f, [nome]: e.target.value })),
    }
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const corpo = {
        ...form,
        data_nascimento: form.data_nascimento || null,
        cpf: form.cpf || null,
        papeis: Object.entries(papeis)
          .filter(([, marcado]) => marcado)
          .map(([nome]) => nome),
      }
      const pessoa = await api.post('/pessoas', corpo)
      navigate(`/pessoas/${pessoa.id}`)
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white px-6 py-4 shadow-sm">
        <Link to="/" className="text-sm text-slate-500 hover:underline">
          ← Voltar para a lista
        </Link>
        <h1 className="text-lg font-bold text-slate-800">Nova pessoa</h1>
      </header>

      <main className="mx-auto max-w-2xl p-6">
        <form
          onSubmit={aoEnviar}
          className="flex flex-col gap-4 rounded-lg bg-white p-6 shadow-sm"
        >
          <Campo label="Nome completo *">
            <input required className={estiloInput} {...campo('nome_completo')} />
          </Campo>

          <div className="grid grid-cols-2 gap-4">
            <Campo label="Data de nascimento">
              <input type="date" className={estiloInput} {...campo('data_nascimento')} />
            </Campo>
            <Campo label="Sexo">
              <select className={estiloInput} {...campo('sexo')}>
                <option value="nao_informado">Não informado</option>
                <option value="feminino">Feminino</option>
                <option value="masculino">Masculino</option>
                <option value="outro">Outro</option>
              </select>
            </Campo>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Campo label="CPF">
              <input
                placeholder="000.000.000-00"
                className={estiloInput}
                {...campo('cpf')}
              />
            </Campo>
            <Campo label="Telefone">
              <input
                placeholder="(21) 99999-9999"
                className={estiloInput}
                {...campo('telefone')}
              />
            </Campo>
          </div>

          <fieldset className="rounded-md border border-slate-200 p-3">
            <legend className="px-1 text-xs font-medium text-slate-500">
              Endereço
            </legend>
            <div className="grid grid-cols-3 gap-3">
              <input
                placeholder="CEP"
                className={`${estiloInput} col-span-1`}
                {...campo('cep')}
              />
              <input
                placeholder="Logradouro"
                className={`${estiloInput} col-span-2`}
                {...campo('logradouro')}
              />
              <input placeholder="Número" className={estiloInput} {...campo('numero')} />
              <input
                placeholder="Complemento"
                className={estiloInput}
                {...campo('complemento')}
              />
              <input placeholder="Bairro" className={estiloInput} {...campo('bairro')} />
              <input
                placeholder="Cidade"
                className={`${estiloInput} col-span-2`}
                {...campo('cidade')}
              />
              <input placeholder="UF" maxLength={2} className={estiloInput} {...campo('uf')} />
            </div>
          </fieldset>

          <Campo label="Como conheceu a casa">
            <input className={estiloInput} {...campo('como_conheceu')} />
          </Campo>

          <fieldset className="flex gap-6">
            <legend className="mb-1 w-full text-xs font-medium text-slate-500">
              Papel
            </legend>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={papeis.assistido}
                onChange={(e) =>
                  setPapeis((p) => ({ ...p, assistido: e.target.checked }))
                }
              />
              Assistido(a) / frequentador(a)
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={papeis.trabalhador}
                onChange={(e) =>
                  setPapeis((p) => ({ ...p, trabalhador: e.target.checked }))
                }
              />
              Trabalhador(a)
            </label>
          </fieldset>

          <Campo label="Observações">
            <textarea
              rows={3}
              className={estiloInput}
              {...campo('observacoes_gerais')}
            />
          </Campo>

          <label className="flex items-start gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              className="mt-1"
              checked={form.consentimento_lgpd}
              onChange={(e) =>
                setForm((f) => ({ ...f, consentimento_lgpd: e.target.checked }))
              }
            />
            A pessoa concorda com o uso dos seus dados pela casa (LGPD).
          </label>

          {erro && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {erro}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Link
              to="/"
              className="rounded-md border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
            >
              Cancelar
            </Link>
            <button
              type="submit"
              disabled={enviando}
              className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {enviando ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}

const estiloInput =
  'w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500'

function Campo({ label, children }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
