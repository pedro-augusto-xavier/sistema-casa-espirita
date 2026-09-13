// Máscaras usadas nos formulários e nas telas de exibição.
// Sempre trabalham a partir dos dígitos -- funcionam tanto pra formatar o que
// a pessoa está digitando quanto pra reformatar o que já veio salvo da API.

export function soDigitos(valor) {
  return (valor || '').replace(/\D/g, '')
}

export function mascaraData(valor) {
  const d = soDigitos(valor).slice(0, 8)
  if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`
  if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`
  return d
}

export function dataParaIso(dataDigitada) {
  const d = soDigitos(dataDigitada)
  if (d.length !== 8) return null
  return `${d.slice(4, 8)}-${d.slice(2, 4)}-${d.slice(0, 2)}`
}

export function isoParaData(iso) {
  if (!iso) return null
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

export function mascaraCpf(valor) {
  const d = soDigitos(valor).slice(0, 11)
  if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
  if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`
  if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`
  return d
}

export const ROTULO_PAPEL = {
  assistido: 'Assistido(a)',
  trabalhador: 'Trabalhador(a)',
  voluntario: 'Voluntário(a)',
}

export const TOM_PAPEL = {
  assistido: 'verde',
  trabalhador: 'ambar',
  voluntario: 'azul',
}

export const ROTULO_VINCULO = {
  pai: 'Pai',
  mae: 'Mãe',
  filho: 'Filho',
  filha: 'Filha',
  conjuge: 'Cônjuge',
  irmao: 'Irmão(ã)',
  avo: 'Avô/Avó',
  neto: 'Neto(a)',
  amigo: 'Amigo(a)',
  responsavel: 'Responsável',
  outro: 'Outro vínculo',
}

// pro seletor de "qual a relação com o responsável" -- sem "responsavel",
// que descreveria a relação inversa (não faz sentido aqui).
export const OPCOES_VINCULO = Object.entries(ROTULO_VINCULO).filter(
  ([valor]) => valor !== 'responsavel',
)

export const ROTULO_ESTADO_CIVIL = {
  solteiro: 'Solteiro(a)',
  casado: 'Casado(a)',
  uniao_estavel: 'União estável',
  divorciado: 'Divorciado(a)',
  viuvo: 'Viúvo(a)',
  nao_informado: null, // não mostra na ficha
}

/** "3 filhos" / "Não tem filhos" / null quando nunca foi perguntado. */
export function rotuloFilhos(quantidade) {
  if (quantidade === null || quantidade === undefined) return null
  if (quantidade === 0) return 'Não tem filhos'
  return quantidade === 1 ? '1 filho' : `${quantidade} filhos`
}

export function mascaraTelefone(valor) {
  const d = soDigitos(valor).slice(0, 11)
  if (d.length > 10) return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}` // celular
  if (d.length > 6) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}` // fixo
  if (d.length > 2) return `(${d.slice(0, 2)}) ${d.slice(2)}`
  return d
}
