// Dicas de senha na hora de digitar. Quem decide de verdade é a API
// (app/core/senhas.py) -- aqui é só pra pessoa não precisar adivinhar.

export const TAMANHO_MINIMO_SENHA = 10

export function dicasDaSenha(senha) {
  return [
    {
      ok: senha.length >= TAMANHO_MINIMO_SENHA,
      texto: `Pelo menos ${TAMANHO_MINIMO_SENHA} caracteres`,
    },
    { ok: /[a-zA-ZÀ-ÿ]/.test(senha), texto: 'Pelo menos uma letra (só números é fácil de descobrir)' },
  ]
}

export function senhaPassaNasDicas(senha) {
  return dicasDaSenha(senha).every((d) => d.ok)
}
