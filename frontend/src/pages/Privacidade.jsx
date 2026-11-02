import { Link } from 'react-router-dom'
import { Emblema } from '../components/Emblema'

/**
 * Política de privacidade -- pública (não precisa de login), pra qualquer
 * pessoa atendida poder ler. Texto em linguagem simples; a base técnica e
 * o inventário completo estão em docs/LGPD.md no repositório.
 */
export function Privacidade() {
  return (
    <div className="min-h-screen bg-stone-100 px-4 py-8 sm:py-12">
      <article className="mx-auto max-w-2xl rounded-2xl bg-white p-6 shadow-sm ring-1 ring-stone-900/5 sm:p-10">
        <header className="flex items-center gap-4 border-b border-stone-100 pb-6">
          <Emblema className="h-14 w-14 shrink-0" />
          <div>
            <h1 className="font-display text-2xl font-semibold text-emerald-950 sm:text-3xl">
              Política de privacidade
            </h1>
            <p className="text-sm text-stone-500">
              Casa Espírita Amor e Perdão · Nova Friburgo – RJ
            </p>
          </div>
        </header>

        <div className="mt-6 flex flex-col gap-6 text-[15px] leading-relaxed text-stone-700">
          <Secao titulo="Quem cuida dos seus dados">
            A Casa Espírita Amor e Perdão é a responsável (controladora, pela Lei Geral de Proteção
            de Dados – LGPD) pelos dados guardados neste sistema interno de cadastro e atendimentos.
          </Secao>

          <Secao titulo="Que dados guardamos">
            <ul className="ml-5 list-disc space-y-1">
              <li>Identificação: nome, data de nascimento, sexo, estado civil, número de filhos.</li>
              <li>Contato: telefone e endereço.</li>
              <li>CPF, só quando você quiser informar (não é obrigatório).</li>
              <li>
                Atendimentos e tratamentos espirituais: datas, tipos de tratamento, quem atendeu,
                observações e o acompanhamento.
              </li>
              <li>
                Pessoas ligadas a você num tratamento (por exemplo, filhos ou pais por quem você
                pediu atendimento) e o tipo de vínculo.
              </li>
              <li>Fotos e documentos que você entregar à casa, se for o caso.</li>
            </ul>
          </Secao>

          <Secao titulo="Dados sensíveis">
            Participar de atendimentos numa casa espírita revela convicção religiosa, e as
            observações podem mencionar saúde. A LGPD chama isso de dado sensível. Por isso, esses
            dados só são registrados com o seu consentimento, anotado na sua ficha, e ficam com
            acesso restrito e protegidos com criptografia.
          </Secao>

          <Secao titulo="Para que usamos">
            Só para organizar e acompanhar os seus atendimentos e tratamentos na casa e para entrar
            em contato sobre eles. Não vendemos, não emprestamos e não usamos seus dados para
            propaganda.
          </Secao>

          <Secao titulo="Quem tem acesso">
            Somente trabalhadores da casa cadastrados no sistema, cada um com login e senha
            próprios. O sistema registra quem entrou, quem consultou e quem alterou cada ficha.
          </Secao>

          <Secao titulo="Onde os dados ficam">
            Em serviços de computação em nuvem contratados para manter o sistema no ar: Neon (banco
            de dados), Render (servidor), Vercel (site) e GitHub (cópias de segurança, criptografadas).
            Esses serviços podem guardar os dados fora do Brasil, seguindo as regras de proteção
            deles. Eles não usam os seus dados para outros fins.
          </Secao>

          <Secao titulo="Como protegemos">
            Conexão sempre criptografada (HTTPS); CPF, observações, anotações dos tratamentos e
            arquivos guardados criptografados; senhas guardadas de forma que nem a casa consegue
            ler; verificação em duas etapas para administradores; registro de acessos; e cópias de
            segurança criptografadas.
          </Secao>

          <Secao titulo="Por quanto tempo">
            Enquanto você for atendido(a) pela casa ou até pedir a exclusão. Quando a ficha é
            excluída, os dados pessoais são apagados e fica só o registro de que houve atendimentos,
            sem identificar você. As cópias de segurança são apagadas automaticamente em até 30
            dias.
          </Secao>

          <Secao titulo="Seus direitos">
            Você pode pedir, a qualquer momento: para saber se temos dados seus e receber uma cópia;
            para corrigir algo errado; para excluir seus dados; e para retirar o consentimento. Basta
            falar pessoalmente com a coordenação da casa. Respondemos em até 15 dias.
          </Secao>

          <Secao titulo="Se algo der errado">
            Se acontecer um incidente de segurança que possa trazer risco a você, a casa avisa você
            e a Autoridade Nacional de Proteção de Dados (ANPD), como manda a lei.
          </Secao>

          <p className="border-t border-stone-100 pt-4 text-xs text-stone-400">
            Última atualização: novembro de 2026.
          </p>
        </div>

        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-1 text-sm text-stone-500 hover:text-emerald-800"
        >
          ← Voltar
        </Link>
      </article>
    </div>
  )
}

function Secao({ titulo, children }) {
  return (
    <section>
      <h2 className="font-display text-lg font-semibold text-emerald-950">{titulo}</h2>
      <div className="mt-1">{children}</div>
    </section>
  )
}
