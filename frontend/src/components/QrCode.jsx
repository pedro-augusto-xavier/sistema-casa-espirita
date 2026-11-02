import qrcode from 'qrcode-generator'
import { useMemo } from 'react'

/** QR code desenhado como SVG pelo próprio React -- sem innerHTML e sem
 * imagem de fora (a CSP do site não deixaria, de qualquer forma). */
export function QrCode({ texto, tamanho = 200 }) {
  const { caminho, total } = useMemo(() => {
    const qr = qrcode(0, 'M')
    qr.addData(texto)
    qr.make()
    const modulos = qr.getModuleCount()
    const margem = 4
    let d = ''
    for (let linha = 0; linha < modulos; linha++) {
      for (let coluna = 0; coluna < modulos; coluna++) {
        if (qr.isDark(linha, coluna)) d += `M${coluna + margem} ${linha + margem}h1v1h-1z`
      }
    }
    return { caminho: d, total: modulos + margem * 2 }
  }, [texto])

  return (
    <svg
      viewBox={`0 0 ${total} ${total}`}
      width={tamanho}
      height={tamanho}
      role="img"
      aria-label="QR code para o aplicativo autenticador"
      shapeRendering="crispEdges"
      className="rounded-lg ring-1 ring-stone-900/10"
    >
      <rect width={total} height={total} fill="#ffffff" />
      <path d={caminho} fill="#000000" />
    </svg>
  )
}
