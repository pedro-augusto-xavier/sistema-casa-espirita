import { jsPDF } from 'jspdf'
import { isoParaData, mascaraTelefone } from './formatadores'

function enderecoDe(pessoa) {
  if (!pessoa) return ''
  return [
    pessoa.logradouro,
    pessoa.numero,
    pessoa.bairro,
    pessoa.cidade && pessoa.uf ? `${pessoa.cidade}/${pessoa.uf}` : pessoa.cidade,
  ]
    .filter(Boolean)
    .join(', ')
}

/**
 * Gera uma folha em PDF por assistido, no mesmo formato da ficha de papel:
 * Nome, DN, Endereço, Tel, Solicitante, nº vezes, Observação, Situação Final,
 * Início e o diário de evolução embaixo.
 */
export function gerarPdfTratamento(tratamento) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const margem = 18
  const largura = doc.internal.pageSize.getWidth() - margem * 2
  const alturaPagina = doc.internal.pageSize.getHeight()

  const assistidos = tratamento.assistidos.length > 0 ? tratamento.assistidos : [null]

  assistidos.forEach((assistido, indice) => {
    if (indice > 0) doc.addPage()
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

    const pessoa = assistido?.pessoa

    linha((tratamento.tipo_nome || '').toUpperCase(), {
      tamanho: 14,
      negrito: true,
      centro: true,
    })
    y += 4

    campo('Nome:', pessoa?.nome_completo)
    campo('DN:', isoParaData(pessoa?.data_nascimento))
    campo('Endereço:', enderecoDe(pessoa))
    campo('Tel:', pessoa?.telefone ? mascaraTelefone(pessoa.telefone) : '')
    campo('Solicitante Atendimento Fraterno:', tratamento.solicitante?.nome_completo)
    campo(
      'Nº vezes:',
      tratamento.sessoes_previstas != null ? String(tratamento.sessoes_previstas) : '',
    )

    y += 2
    linha('Observação', { negrito: true })
    linha(tratamento.observacao || '—')

    y += 2
    linha('Situação Final', { negrito: true })
    linha(assistido?.situacao_final || tratamento.situacao_final || '—')

    y += 2
    campo('Início:', isoParaData(tratamento.data_inicio))

    y += 4
    quebrarSeNecessario(6)
    doc.setDrawColor('#cbd5e1')
    doc.line(margem, y, margem + largura, y)
    y += 8

    linha('Diário de evolução', { tamanho: 12, negrito: true })
    y += 2

    if (tratamento.evolucoes.length === 0) {
      linha('Nenhuma anotação ainda.')
    }
    tratamento.evolucoes.forEach((e) => {
      quebrarSeNecessario(10)
      linha(
        `${isoParaData(e.data)}${e.registrado_por ? ' — ' + e.registrado_por.nome_completo : ''}`,
        { negrito: true },
      )
      linha(e.texto)
      y += 3
    })
  })

  const primeiroNome = tratamento.assistidos[0]?.pessoa?.nome_completo
  const nomeArquivo = primeiroNome
    ? `tratamento-${primeiroNome.replace(/\s+/g, '_')}`
    : `tratamento-${tratamento.id}`
  doc.save(`${nomeArquivo}.pdf`)
}
