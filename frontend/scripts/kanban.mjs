#!/usr/bin/env node
// Helper del Kanban Frontend.
// Muestra el estado de un issue en el tablero y el comando para moverlo de estado.
// Uso: node scripts/kanban.mjs <numero-de-issue>
// Requiere `gh` instalado y autenticado.

import { execSync } from 'node:child_process'

const OWNER = 'help-chair'
const PROJECT_NUMBER = 16

function gh(args) {
  return execSync(`gh ${args}`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
}

function listJson(command) {
  try {
    return JSON.parse(gh(command))
  } catch {
    return null
  }
}

const issue = Number(process.argv[2])
if (!Number.isInteger(issue) || issue < 1) {
  console.error('Uso: node scripts/kanban.mjs <numero-de-issue>')
  process.exit(1)
}

// 1) Id de nodo del proyecto (lo pide `gh project item-edit`).
const projects = listJson(`project list --owner ${OWNER} --format json`)
const project = projects?.projects?.find((p) => p.number === PROJECT_NUMBER)
if (!project?.id) {
  console.error(`No se encontró el proyecto número ${PROJECT_NUMBER} de ${OWNER}.`)
  process.exit(1)
}

// 2) Campo Status y sus opciones.
const fields = listJson(`project field-list ${PROJECT_NUMBER} --owner ${OWNER} --format json`)
const statusField = fields?.fields?.find((f) => f.name === 'Status' && Array.isArray(f.options))
if (!statusField) {
  console.error('No se encontró el campo "Status" del proyecto.')
  process.exit(1)
}

// 3) Buscar el issue en el tablero.
const items = listJson(`project item-list ${PROJECT_NUMBER} --owner ${OWNER} --format json --limit 100`)
const item = items?.items?.find((it) => it.content?.number === issue)

if (!item) {
  console.log(`El issue #${issue} no está en el tablero.`)
  console.log(
    `\nPara agregarlo:\n  gh project item-add ${PROJECT_NUMBER} --owner ${OWNER} --url https://github.com/${OWNER}/${OWNER}/issues/${issue}`,
  )
} else {
  console.log(`#${issue} está en el tablero con estado: ${item.status}`)
  console.log('\nPara moverlo de estado:')
  for (const option of statusField.options) {
    console.log(
      `  ${option.name}: gh project item-edit --id ${item.id} --project-id ${project.id} --field-id ${statusField.id} --single-select-option-id ${option.id}`,
    )
  }
}
