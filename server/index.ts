import { spawn } from 'child_process';
import { resolve } from 'path';

const pythonProcess = spawn('python', ['main.py'], {
  cwd: resolve(import.meta.dirname, 'python'),
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
