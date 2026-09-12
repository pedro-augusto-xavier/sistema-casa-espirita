import { jsPDF } from 'jspdf'
import { isoParaData, mascaraTelefone } from './formatadores'

const ROTULO_MODALIDADE = {
  presencial: 'Presencial',
  video: 'Vídeo',
  distancia: 'À distância',
}

function enderecoDe(pessoa) {
  return [
    pessoa.logradouro,
    pessoa.numero,
    pessoa.bairro,
    pessoa.cidade && pessoa.uf ? `${pessoa.cidade}/${pessoa.uf}` : pessoa.cidade,
  ]
    .filter(Boolean)
    .join(', ')
}

/** Gera o PDF de um atendimento (visita avulsa), no estilo da ficha de papel. */
export function gerarPdfAtendimento(atendimento) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const margem = 18
  const largura = doc.internal.pageSize.getWidth() - margem * 2
  const alturaPagina = doc.internal.pageSize.getHeight()
  let y = margem

  function quebrarSeNecessario(proximaAltura) {
    if (y + proximaAltura > alturaPagina - margem) {
      doc.addPage()
      y = margem
    }
  }

  function linha(txt, { tamanho = 10, negrito = false, centro = false } = {}) {
    doc.setFont('helvetica', negrito ? 'bold' : 'normal')
    doc.setFontSize(tamanho)
    doc.setTextColor('#1e293b')
    doc.splitTextToSize(txt || '', largura).forEach((parte) => {
      quebrarSeNecessario(tamanho / 2 + 2)
      doc.text(parte, centro ? margem + largura / 2 : margem, y, {
        align: centro ? 'center' : 'left',
      })
      y += tamanho / 2 + 2
    })
  }

  function campo(rotulo, valor) {
    quebrarSeNecessario(8)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor('#1e293b')
    doc.text(rotulo, margem, y)
    const largRotulo = doc.getTextWidth(`${rotulo} `)
    doc.text(valor || '', margem + largRotulo, y)
    doc.setDrawColor('#94a3b8')
    doc.line(margem + largRotulo, y + 1.2, margem + largura, y + 1.2)
    y += 8
  }

  linha('FICHA DE ATENDIMENTO', { tamanho: 14, negrito: true, centro: true })
  y += 4

  campo('Data:', isoParaData(atendimento.data))
  campo('Modalidade:', ROTULO_MODALIDADE[atendimento.modalidade])
  campo('Atendido por:', atendimento.atendido_por?.nome_completo)
  if (!atendimento.presente) {
    campo('Solicitante:', atendimento.solicitante?.nome_completo)
  }

  y += 2
  campo('Nome:', atendimento.pessoa.nome_completo)
  campo('Nascimento:', isoParaData(atendimento.pessoa.data_nascimento))
  campo('Endereço:', enderecoDe(atendimento.pessoa))
  campo(
    'Tel:',
    atendimento.pessoa.telefone ? mascaraTelefone(atendimento.pessoa.telefone) : '',
  )

  y += 2
  linha('Tratamentos', { negrito: true })
  if (atendimento.tratamentos.length === 0) {
    linha('Nenhum tratamento marcado.')
  }
  atendimento.tratamentos.forEach((t) => {
    let texto = `- ${t.tipo_tratamento_nome}`
    if (t.modalidade) texto += ` (${ROTULO_MODALIDADE[t.modalidade]})`
    if (t.sessoes_previstas) {
      texto += ` — ${t.sessoes_realizadas}/${t.sessoes_previstas} sessões`
    }
    linha(texto)
    if (t.observacao) linha(`  ${t.observacao}`, { tamanho: 9 })
  })

  y += 2
  linha('Observação', { negrito: true })
  linha(atendimento.observacao || '—')

  const dataArquivo = atendimento.data
  doc.save(
    `atendimento-${atendimento.pessoa.nome_completo.replace(/\s+/g, '_')}-${dataArquivo}.pdf`,
  )
}
