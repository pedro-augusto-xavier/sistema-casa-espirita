import { useState } from 'react'
import { dataParaIso, mascaraCpf, mascaraData, mascaraTelefone } from '../utils/formatadores'
import { Botao, BotaoLink, MensagemErro } from './ui'

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
      setErro('Data de nascimento inválida — use o formato dd/mm/aaaa.')
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
    <form
      onSubmit={aoEnviar}
      className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-stone-900/5"
    >
      <div className="h-1.5 bg-linear-to-r from-emerald-800 via-emerald-600 to-amber-500" />

      <div className="flex flex-col gap-8 p-6 sm:p-8">
        {/* ---------- identificação ---------- */}
        <Secao titulo="Identificação">
          <Campo label="Nome completo" obrigatorio>
            <input required autoFocus className="campo" {...campo('nome_completo')} />
          </Campo>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Campo label="Data de nascimento" obrigatorio>
              <input
                required
                inputMode="numeric"
                placeholder="dd/mm/aaaa"
                maxLength={10}
                value={form.data_nascimento}
                onChange={(e) =>
                  setForm((f) => ({ ...f, data_nascimento: mascaraData(e.target.value) }))
                }
                className="campo"
              />
            </Campo>
            <Campo label="Sexo" obrigatorio>
              <select required className="campo" {...campo('sexo')}>
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Campo label="CPF" obrigatorio>
              <input
                required
                inputMode="numeric"
                placeholder="000.000.000-00"
                maxLength={14}
                value={form.cpf}
                onChange={(e) => setForm((f) => ({ ...f, cpf: mascaraCpf(e.target.value) }))}
                className="campo"
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
                className="campo"
              />
            </Campo>
          </div>
        </Secao>

        {/* ---------- endereço ---------- */}
        <Secao titulo="Endereço" descricao="Opcional">
          <div className="grid grid-cols-6 gap-3">
            <input placeholder="CEP" className="campo col-span-2" {...campo('cep')} />
            <input placeholder="Logradouro" className="campo col-span-4" {...campo('logradouro')} />
            <input placeholder="Número" className="campo col-span-2" {...campo('numero')} />
            <input
              placeholder="Complemento"
              className="campo col-span-4"
              {...campo('complemento')}
            />
            <input placeholder="Bairro" className="campo col-span-6 sm:col-span-2" {...campo('bairro')} />
            <input placeholder="Cidade" className="campo col-span-4 sm:col-span-3" {...campo('cidade')} />
            <input
              placeholder="UF"
              maxLength={2}
              className="campo col-span-2 uppercase sm:col-span-1"
              {...campo('uf')}
            />
          </div>
        </Secao>

        {/* ---------- na casa ---------- */}
        <Secao titulo="Na casa">
          <Campo label="Como conheceu a casa">
            <input className="campo" {...campo('como_conheceu')} />
          </Campo>

          <fieldset>
            <legend className="text-sm font-medium text-stone-700">Papel</legend>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <Opcao
                marcado={papeis.assistido}
                onChange={(v) => setPapeis((p) => ({ ...p, assistido: v }))}
                titulo="Assistido(a)"
                descricao="Recebe atendimento ou frequenta a casa"
              />
              <Opcao
                marcado={papeis.trabalhador}
                onChange={(v) => setPapeis((p) => ({ ...p, trabalhador: v }))}
                titulo="Trabalhador(a)"
                descricao="Atende, dirige grupos ou participa da escala"
              />
            </div>
          </fieldset>

          <Campo label="Observações">
            <textarea rows={3} className="campo" {...campo('observacoes_gerais')} />
          </Campo>
        </Secao>

        <MensagemErro>{erro}</MensagemErro>
      </div>

      <div className="flex justify-end gap-2 border-t border-stone-100 bg-stone-50/60 px-6 py-4 sm:px-8">
        <BotaoLink to={linkCancelar} variante="secundario">
          Cancelar
        </BotaoLink>
        <Botao type="submit" disabled={enviando}>
          {enviando ? 'Salvando...' : textoBotao}
        </Botao>
      </div>
    </form>
  )
}

function Secao({ titulo, descricao, children }) {
  return (
    <section>
      <div className="mb-4 flex items-baseline gap-2">
        <h3 className="font-display text-lg font-semibold text-emerald-950">{titulo}</h3>
        {descricao && <span className="text-xs text-stone-400">{descricao}</span>}
      </div>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  )
}

function Campo({ label, obrigatorio, children }) {
  return (
    <label className="block text-sm font-medium text-stone-700">
      {label}
      {obrigatorio && <span className="ml-0.5 text-amber-600">*</span>}
      <div className="mt-1">{children}</div>
    </label>
  )
}

/** Checkbox em forma de cartão, com título e descrição. */
function Opcao({ marcado, onChange, titulo, descricao }) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
        marcado
          ? 'border-emerald-600 bg-emerald-50/60 ring-1 ring-emerald-600'
          : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50'
      }`}
    >
      <input
        type="checkbox"
        checked={marcado}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 accent-emerald-700"
      />
      <span>
        <span className="block text-sm font-medium text-stone-800">{titulo}</span>
        <span className="block text-xs text-stone-500">{descricao}</span>
      </span>
    </label>
  )
}
