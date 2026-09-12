import { useState } from 'react'
import { Link } from 'react-router-dom'
import { dataParaIso, mascaraCpf, mascaraData, mascaraTelefone } from '../utils/formatadores'

export const CAMPOS_VAZIOS = {
  nome_completo: '',
  data_nascimento: '', // dd/mm/aaaa, digitado
  sexo: '',
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
}

/** Formulário de Pessoa, usado tanto no cadastro quanto na edição. */
export function PessoaForm({
  valoresIniciais = CAMPOS_VAZIOS,
  papeisIniciais = { trabalhador: false, assistido: true },
  aoSalvar,
  linkCancelar,
  textoBotao = 'Salvar',
}) {
  const [form, setForm] = useState(valoresIniciais)
  const [papeis, setPapeis] = useState(papeisIniciais)
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

    const nascimentoIso = dataParaIso(form.data_nascimento)
    if (!nascimentoIso) {
      setErro('Data de nascimento inválida -- use o formato dd/mm/aaaa.')
      return
    }

    setEnviando(true)
    try {
      const corpo = {
        ...form,
        data_nascimento: nascimentoIso,
        cpf: form.cpf || null,
        papeis: Object.entries(papeis)
          .filter(([, marcado]) => marcado)
          .map(([nome]) => nome),
      }
      await aoSalvar(corpo)
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={aoEnviar} className="flex flex-col gap-4 rounded-lg bg-white p-6 shadow-sm ring-1 ring-stone-900/5">
      <Campo label="Nome completo *">
        <input required className={estiloInput} {...campo('nome_completo')} />
      </Campo>

      <div className="grid grid-cols-2 gap-4">
        <Campo label="Data de nascimento *">
          <input
            required
            inputMode="numeric"
            placeholder="dd/mm/aaaa"
            maxLength={10}
            value={form.data_nascimento}
            onChange={(e) =>
              setForm((f) => ({ ...f, data_nascimento: mascaraData(e.target.value) }))
            }
            className={estiloInput}
          />
        </Campo>
        <Campo label="Sexo *">
          <select required className={estiloInput} {...campo('sexo')}>
            <option value="" disabled>
              Selecione...
            </option>
            <option value="feminino">Feminino</option>
            <option value="masculino">Masculino</option>
            <option value="outro">Outro</option>
            <option value="nao_informado">Prefere não informar</option>
          </select>
        </Campo>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Campo label="CPF *">
          <input
            required
            inputMode="numeric"
            placeholder="000.000.000-00"
            maxLength={14}
            value={form.cpf}
            onChange={(e) => setForm((f) => ({ ...f, cpf: mascaraCpf(e.target.value) }))}
            className={estiloInput}
          />
        </Campo>
        <Campo label="Telefone">
          <input
            inputMode="numeric"
            placeholder="(00) 00000-0000"
            maxLength={15}
            value={form.telefone}
            onChange={(e) =>
              setForm((f) => ({ ...f, telefone: mascaraTelefone(e.target.value) }))
            }
            className={estiloInput}
          />
        </Campo>
      </div>

      <fieldset className="rounded-md border border-stone-200 p-3">
        <legend className="px-1 text-xs font-medium text-stone-500">
          Endereço (opcional)
        </legend>
        <div className="grid grid-cols-3 gap-3">
          <input placeholder="CEP" className={`${estiloInput} col-span-1`} {...campo('cep')} />
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
        <legend className="mb-1 w-full text-xs font-medium text-stone-500">Papel</legend>
        <label className="flex items-center gap-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={papeis.assistido}
            onChange={(e) => setPapeis((p) => ({ ...p, assistido: e.target.checked }))}
          />
          Assistido(a) / frequentador(a)
        </label>
        <label className="flex items-center gap-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={papeis.trabalhador}
            onChange={(e) => setPapeis((p) => ({ ...p, trabalhador: e.target.checked }))}
          />
          Trabalhador(a)
        </label>
      </fieldset>

      <Campo label="Observações">
        <textarea rows={3} className={estiloInput} {...campo('observacoes_gerais')} />
      </Campo>

      {erro && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Link
          to={linkCancelar}
          className="rounded-md border border-stone-300 px-4 py-2 text-sm hover:bg-stone-50"
        >
          Cancelar
        </Link>
        <button
          type="submit"
          disabled={enviando}
          className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {enviando ? 'Salvando...' : textoBotao}
        </button>
      </div>
    </form>
  )
}

const estiloInput =
  'w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15'

function Campo({ label, children }) {
  return (
    <label className="block text-sm font-medium text-stone-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
