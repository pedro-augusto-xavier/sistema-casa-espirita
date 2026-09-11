import { jsPDF } from 'jspdf'
import { isoParaData, mascaraCpf, mascaraTelefone } from './formatadores'

const ROTULO_TIPO = {
  atendimento: 'Atendimento',
  tratamento_inicio: 'Início de tratamento',
  evolucao: 'Evolução',
  grupo: 'Grupo',
}

/** Monta um PDF da ficha (dados + histórico) e dispara o download. */
export function gerarPdfFicha(pessoa, historico) {
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

  function texto(txt, { tamanho = 10, negrito = false, cor = '#1e293b' } = {}) {
    doc.setFont('helvetica', negrito ? 'bold' : 'normal')
    doc.setFontSize(tamanho)
    doc.setTextColor(cor)
    const linhas = doc.splitTextToSize(txt, largura)
    linhas.forEach((linha) => {
      quebrarSeNecessario(tamanho / 2 + 2)
      doc.text(linha, margem, y)
      y += tamanho / 2 + 2
    })
  }

  function linhaDado(rotulo, valor) {
    if (!valor) return
    texto(`${rotulo}: ${valor}`)
  }

  texto('Casa Espírita', { tamanho: 11, cor: '#64748b' })
  texto(pessoa.nome_completo, { tamanho: 18, negrito: true })
  y += 3

  linhaDado('Nascimento', isoParaData(pessoa.data_nascimento))
  linhaDado('CPF', pessoa.cpf && mascaraCpf(pessoa.cpf))
  linhaDado('Telefone', pessoa.telefone && mascaraTelefone(pessoa.telefone))
  linhaDado('Como conheceu', pessoa.como_conheceu)
  linhaDado(
    'Endereço',
    [
      pessoa.logradouro,
      pessoa.numero,
      pessoa.bairro,
      pessoa.cidade && pessoa.uf ? `${pessoa.cidade}/${pessoa.uf}` : pessoa.cidade,
    ]
      .filter(Boolean)
      .join(', '),
  )
  if (pessoa.observacoes_gerais) linhaDado('Observações', pessoa.observacoes_gerais)

  y += 4
  quebrarSeNecessario(6)
  doc.setDrawColor('#cbd5e1')
  doc.line(margem, y, margem + largura, y)
  y += 8

  texto('Histórico', { tamanho: 13, negrito: true })
  y += 2

  if (historico.length === 0) {
    texto('Nenhum atendimento ou tratamento registrado.', { tamanho: 10, cor: '#64748b' })
  }

  historico.forEach((item) => {
    quebrarSeNecessario(10)
    texto(`${isoParaData(item.data)} — ${ROTULO_TIPO[item.tipo] ?? item.tipo}`, {
      negrito: true,
    })
    texto(item.titulo)
    if (item.descricao) {
      texto(item.descricao, { tamanho: 9, cor: '#475569' })
    }
    y += 3
  })

  doc.save(`ficha-${pessoa.nome_completo.replace(/\s+/g, '_')}.pdf`)
}
