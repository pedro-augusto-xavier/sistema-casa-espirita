// Rodapé de aviso em todo PDF gerado pelo sistema: quem imprime ou manda o
// arquivo pra frente precisa saber que ali tem dado pessoal sensível.

export const AVISO_LGPD =
  'Documento com dados pessoais sensíveis (LGPD). Uso interno da Casa Espírita Amor e Perdão: ' +
  'não compartilhe, guarde em local seguro e descarte picotado.'

/** Escreve o aviso no pé de todas as páginas do documento jsPDF. */
export function carimbarAvisoLgpd(doc) {
  const largura = doc.internal.pageSize.getWidth()
  const altura = doc.internal.pageSize.getHeight()
  const total = doc.getNumberOfPages()
  for (let pagina = 1; pagina <= total; pagina++) {
    doc.setPage(pagina)
    doc.setFont('helvetica', 'italic')
    doc.setFontSize(7)
    doc.setTextColor('#64748b')
    const linhas = doc.splitTextToSize(AVISO_LGPD, largura - 36)
    doc.text(linhas, largura / 2, altura - 10, { align: 'center' })
    if (total > 1) doc.text(`${pagina}/${total}`, largura - 18, altura - 4, { align: 'right' })
  }
}
