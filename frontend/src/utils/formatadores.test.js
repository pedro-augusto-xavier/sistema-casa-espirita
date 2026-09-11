import { describe, expect, it } from 'vitest'
import {
  dataParaIso,
  isoParaData,
  mascaraCpf,
  mascaraData,
  mascaraTelefone,
  soDigitos,
} from './formatadores'

describe('soDigitos', () => {
  it('remove tudo que não for dígito', () => {
    expect(soDigitos('(21) 99999-8888')).toBe('21999998888')
  })

  it('lida com valor vazio ou indefinido', () => {
    expect(soDigitos('')).toBe('')
    expect(soDigitos(undefined)).toBe('')
  })
})

describe('mascaraData', () => {
  it('formata os dígitos como dd/mm/aaaa conforme a pessoa digita', () => {
    expect(mascaraData('23')).toBe('23')
    expect(mascaraData('2309')).toBe('23/09')
    expect(mascaraData('23091958')).toBe('23/09/1958')
  })

  it('ignora caracteres que não são dígito na entrada', () => {
    expect(mascaraData('23/09/1958')).toBe('23/09/1958')
  })

  it('corta em 8 dígitos', () => {
    expect(mascaraData('230919589999')).toBe('23/09/1958')
  })
})

describe('dataParaIso', () => {
  it('converte dd/mm/aaaa para aaaa-mm-dd', () => {
    expect(dataParaIso('23/09/1958')).toBe('1958-09-23')
  })

  it('retorna null quando a data está incompleta', () => {
    expect(dataParaIso('23/09')).toBeNull()
    expect(dataParaIso('')).toBeNull()
  })
})

describe('isoParaData', () => {
  it('converte aaaa-mm-dd para dd/mm/aaaa', () => {
    expect(isoParaData('1958-09-23')).toBe('23/09/1958')
  })

  it('retorna null para valor vazio', () => {
    expect(isoParaData(null)).toBeNull()
    expect(isoParaData('')).toBeNull()
  })
})

describe('mascaraCpf', () => {
  it('formata progressivamente conforme a quantidade de dígitos', () => {
    expect(mascaraCpf('390')).toBe('390')
    expect(mascaraCpf('390533')).toBe('390.533')
    expect(mascaraCpf('390533447')).toBe('390.533.447')
    expect(mascaraCpf('39053344705')).toBe('390.533.447-05')
  })

  it('ignora dígitos além do 11º', () => {
    expect(mascaraCpf('390533447059999')).toBe('390.533.447-05')
  })

  it('reformata um valor que já vem com pontuação (ex: vindo da API)', () => {
    expect(mascaraCpf('39053344705')).toBe(mascaraCpf('390.533.447-05'))
  })
})

describe('mascaraTelefone', () => {
  it('formata celular (11 dígitos)', () => {
    expect(mascaraTelefone('21999998888')).toBe('(21) 99999-8888')
  })

  it('formata fixo (10 dígitos)', () => {
    expect(mascaraTelefone('2133334444')).toBe('(21) 3333-4444')
  })

  it('formata progressivamente enquanto a pessoa digita', () => {
    expect(mascaraTelefone('21')).toBe('21')
    expect(mascaraTelefone('219')).toBe('(21) 9')
  })
})
