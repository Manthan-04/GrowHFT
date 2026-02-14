import * as esbuild from "esbuild";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { copyFileSync, mkdirSync, cpSync, existsSync } from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, "..");

esbuild.buildSync({
  entryPoints: ["server/index.ts"],
  outfile: "dist/index.cjs",
  platform: "node",
  format: "cjs",
  bundle: true,
  external: ["child_process", "path", "url"],
});

const srcPython = resolve(rootDir, "server/python");
const dstPython = resolve(rootDir, "dist/python");

if (existsSync(srcPython)) {
  cpSync(srcPython, dstPython, { recursive: true });
}

console.log("Build complete: dist/index.cjs + dist/python/");
