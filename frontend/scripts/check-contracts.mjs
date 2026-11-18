#!/usr/bin/env node

import { execSync } from 'node:child_process';
import path from 'node:path';

// Mapeo oficial según .github/CODEOWNERS e ITIL v4
const OWNERS_MAP = {
  events: {
    name: 'Gestión de Eventos (Equipo 1)',
    owners: '@Alexis-sillyprogrammer, @DonitaCosmica',
    frontendPath: 'frontend/src/features/events/',
    typesPath: 'frontend/src/features/events/types.ts',
  },
  access: {
    name: 'Gestión de Accesos (Equipo 2)',
    owners: '@JohanPEBO, @spartan117alan1',
    frontendPath: 'frontend/src/features/access/',
    typesPath: 'frontend/src/features/access/types.ts',
  },
  requests: {
    name: 'Gestión de Peticiones (Equipo 3)',
    owners: '@Zteven, @ivan0407mv',
    frontendPath: 'frontend/src/features/requests/',
    typesPath: 'frontend/src/features/requests/types.ts',
  },
  incidents: {
    name: 'Gestión de Incidencias (Equipo 4)',
    owners: '@DiegoMH890, @decko67',
    frontendPath: 'frontend/src/features/incidents/',
    typesPath: 'frontend/src/features/incidents/types.ts',
  },
  problems: {
    name: 'Gestión de Problemas (Equipo 5)',
    owners: '@Leon2411, @PabloH126',
    frontendPath: 'frontend/src/features/problems/',
    typesPath: 'frontend/src/features/problems/types.ts',
  },
  knowledge: {
    name: 'Base de Conocimiento (Equipo 5)',
    owners: '@Leon2411, @PabloH126',
    frontendPath: 'frontend/src/features/knowledge/',
    typesPath: 'frontend/src/features/knowledge/types.ts',
  },
  gateway: {
    name: 'Plataforma / Gateway (Equipo 7)',
    owners: '@DonitaCosmica, @decko67',
    frontendPath: 'frontend/src/features/public/',
    typesPath: 'frontend/src/api/public.ts',
  },
};

function getChangedFiles() {
  try {
    // Intenta comparar tras un git pull/merge (ORIG_HEAD vs HEAD)
    return execSync('git diff ORIG_HEAD HEAD --name-only', { encoding: 'utf-8' })
      .trim()
      .split('\n')
      .filter(Boolean);
  } catch {
    try {
      // Alternativa: último commit
      return execSync('git diff HEAD~1 HEAD --name-only', { encoding: 'utf-8' })
        .trim()
        .split('\n')
        .filter(Boolean);
    } catch {
      return [];
    }
  }
}

const files = getChangedFiles();
const affectedModules = new Set();

for (const file of files) {
  const normalized = file.replace(/\\/g, '/');
  for (const mod of Object.keys(OWNERS_MAP)) {
    if (
      normalized.startsWith(`contracts/${mod}/`) ||
      normalized.startsWith(`services/${mod}/`)
    ) {
      affectedModules.add(mod);
    }
  }
}

if (affectedModules.size === 0) {
  console.log('\x1b[32m✔ [Frontend Sync]: No se detectaron cambios en contratos ni servicios backend en esta actualización.\x1b[0m');
  process.exit(0);
}

console.log('\n\x1b[1m\x1b[33m' + '='.repeat(80));
console.log('🔔 [HELP CHAIR · AVISO DE SINCRONIZACIÓN DE CONTRATOS]');
console.log('='.repeat(80) + '\x1b[0m\n');
console.log('Se detectaron cambios recientes en el backend o contratos de los siguientes módulos:\n');

for (const mod of affectedModules) {
  const info = OWNERS_MAP[mod];
  console.log(`\x1b[36m📦 Módulo: ${info.name}\x1b[0m`);
  console.log(`   • Responsables (.github/CODEOWNERS): \x1b[35m${info.owners}\x1b[0m`);
  console.log(`   • Contrato: \x1b[33mcontracts/${mod}/openapi.yaml\x1b[0m`);
  console.log(`   • Archivo de tipos a revisar: \x1b[32m${info.typesPath}\x1b[0m`);
  console.log(`   • Carpeta Frontend: \x1b[34m${info.frontendPath}\x1b[0m\n`);
}

console.log('\x1b[33m👉 ACCIÓN RECOMENDADA:');
console.log('   Si eres desarrollador de Frontend, verifica si cambiaron propiedades,');
console.log('   endpoints o tipos en el contrato antes de continuar con la interfaz.\x1b[0m\n');
console.log('\x1b[33m' + '='.repeat(80) + '\x1b[0m\n');
