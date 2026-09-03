import path from "node:path";

export function resolveVaultRoot(): string {
  return path.resolve(process.env.EVO_STORE ?? path.join(process.cwd(), "..", "data"));
}

export function assertInsideVault(filePath: string): string {
  const resolved = path.resolve(filePath);
  const vaultRoot = resolveVaultRoot();
  if (!resolved.startsWith(vaultRoot + path.sep)) {
    throw new Error(`Path outside vault: ${resolved}`);
  }
  return resolved;
}
