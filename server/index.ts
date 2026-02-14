import { spawn } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const currentDir = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const pythonProcess = spawn('python', ['main.py'], {
  cwd: resolve(currentDir, 'python'),
  stdio: 'inherit',
  env: { ...process.env },
});

pythonProcess.on('error', (err) => {
  console.error('Failed to start Python server:', err);
  process.exit(1);
});

pythonProcess.on('exit', (code) => {
  process.exit(code ?? 0);
});
