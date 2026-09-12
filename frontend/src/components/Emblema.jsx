// Ângulos (em graus) de cada folha da coroa de louros, medidos a partir do topo
// do círculo, girando no sentido horário. Deixamos um vão no topo (de -25° a 25°)
// como um pequeno respiro decorativo.
const ANGULOS_FOLHAS = [25, 48, 71, 94, 117, 140, 163, 335, 312, 289, 266, 243, 220, 197]

/**
 * Emblema decorativo da casa: um selo simples com coroa de louros e uma
 * rosa estilizada no centro, desenhado em SVG puro -- espaço reservado até
 * termos o arquivo de imagem do brasão de verdade.
 */
export function Emblema({ className = 'h-14 w-14' }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      <circle cx="50" cy="50" r="47" fill="none" className="stroke-emerald-700" strokeWidth="1.5" />
      <circle
        cx="50"
        cy="50"
        r="41"
        fill="none"
        className="stroke-emerald-700/40"
        strokeWidth="1"
      />

      <g className="fill-emerald-700">
        {ANGULOS_FOLHAS.map((angulo) => (
          <ellipse
            key={angulo}
            cx="50"
            cy="15"
            rx="3.4"
            ry="8"
            transform={`rotate(${angulo} 50 50)`}
          />
        ))}
      </g>

      <g className="fill-amber-600">
        <circle cx="50" cy="44" r="3.4" />
        <circle cx="44.5" cy="48" r="3.4" />
        <circle cx="55.5" cy="48" r="3.4" />
        <circle cx="46.2" cy="54" r="3.4" />
        <circle cx="53.8" cy="54" r="3.4" />
      </g>
      <circle cx="50" cy="49.5" r="2.4" className="fill-amber-800" />
    </svg>
  )
}
