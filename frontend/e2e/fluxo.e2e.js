import { expect, test } from '@playwright/test'

// O caminho de todo dia: entrar, cadastrar uma ficha e registrar um
// atendimento. O usuário vem de `python -m tests.e2e_preparar`.

test('entrar, cadastrar ficha e registrar atendimento', async ({ page }) => {
  const nome = `Pessoa Teste ${Date.now()}`

  await page.goto('/login')
  await page.getByLabel('Nome').fill('Operador E2E')
  await page.getByLabel('Senha').fill(process.env.E2E_SENHA)
  await page.getByRole('button', { name: 'Entrar' }).click()

  await page.getByRole('link', { name: '+ Nova pessoa' }).first().click()
  await page.getByLabel('Nome completo').fill(nome)
  await page.getByLabel('Data de nascimento').fill('01/01/1980')
  await page.getByLabel('Sexo').selectOption('feminino')
  await page.getByRole('button', { name: 'Salvar ficha' }).click()

  await expect(page).toHaveURL(/\/pessoas\/\d+$/)
  await expect(page.getByRole('heading', { name: nome })).toBeVisible()

  await page.getByRole('button', { name: '+ Registrar atendimento' }).first().click()
  await page.getByLabel('Observação').fill('Atendimento do teste automático.')
  await page.getByRole('button', { name: 'Registrar', exact: true }).click()

  await expect(page.getByRole('heading', { name: 'Nenhum atendimento ainda' })).toHaveCount(0)
  await expect(page.getByText('Atendimento do teste automático.')).toBeVisible()
})
