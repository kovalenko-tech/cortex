#!/usr/bin/env node
const { execSync } = require('child_process');
function findPython() {
  for (const cmd of ['python3.11', 'python3.12', 'python3.13', 'python3', 'python']) {
    try { execSync(`${cmd} -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"`, { stdio: 'pipe' }); return cmd; } catch {}
  }
  return null;
}
if (!findPython()) {
  console.warn('\n⚠️  cortex-ai: Python 3.11+ not found. Install from https://python.org/downloads\n');
}
