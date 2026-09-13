import logo from '../assets/logo.jpg'

/**
 * A logo de verdade da Casa Espírita Amor e Perdão. `className` controla
 * o tamanho em todo lugar que ela aparece (login, cabeçalho, marca d'água,
 * estados vazios) -- é só passar a altura/largura desejada.
 */
export function Emblema({ className = 'h-14 w-14' }) {
  return (
    <img
      src={logo}
      alt="Casa Espírita Amor e Perdão"
      className={`object-contain ${className}`}
    />
  )
}
