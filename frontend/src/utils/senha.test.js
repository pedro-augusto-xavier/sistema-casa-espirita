import { describe, expect, it } from 'vitest'
import { dicasDaSenha, senhaPassaNasDicas } from './senha'

describe('dicas de senha', () => {
  it('recusa senha curta', () => {
    expect(senhaPassaNasDicas('abc12')).toBe(false)
  })

  it('recusa senha só de números (CPF, telefone)', () => {
    expect(senhaPassaNasDicas('39053344705')).toBe(false)
  })

  it('aceita frase com 10+ caracteres', () => {
    expect(senhaPassaNasDicas('girassol amarelo')).toBe(true)
  })

  it('aceita letra acentuada como letra', () => {
    expect(senhaPassaNasDicas('ção1234567')).toBe(true)
  })

  it('marca cada dica separadamente', () => {
    const [tamanho, letra] = dicasDaSenha('1234567890')
    expect(tamanho.ok).toBe(true)
    expect(letra.ok).toBe(false)
  })
})
