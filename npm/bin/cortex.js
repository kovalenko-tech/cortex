#!/usr/bin/env node
const { execSync, spawnSync } = require('child_process');

function findPython() {
  for (const cmd of ['python3.11', 'python3.12', 'python3.13', 'python3', 'python']) {
    try {
      execSync(`${cmd} -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"`, { stdio: 'pipe' });
      return cmd;
    } catch {}
  }
  return null;
}

function isCortexInstalled(python) {
  try { execSync(`${python} -m cortex --version`, { stdio: 'pipe' }); return true; } catch { return false; }
}

function installCortex(python) {
  console.log('Installing cortex...');
  try {
    execSync(`${python} -m pip install git+https://github.com/kovalenko-tech/cortex.git --quiet`, { stdio: 'inherit' });
    return true;
  } catch { return false; }
}

const python = findPython();
if (!python) {
  console.error('Error: Python 3.11+ is required. Install from https://python.org/downloads');
  process.exit(1);
}
if (!isCortexInstalled(python)) {
  if (!installCortex(python)) { console.error('Error: Failed to install cortex.'); process.exit(1); }
}
const result = spawnSync(python, ['-m', 'cortex', ...process.argv.slice(2)], { stdio: 'inherit', env: process.env });
process.exit(result.status || 0);
