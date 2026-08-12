import { getCloudflareContext } from "@opennextjs/cloudflare";

type ControlApiService = {
  fetch(request: Request): Promise<Response>;
};

export async function fetchControlApi(path: string, init?: RequestInit): Promise<Response> {
  const service = await controlApiService();
  if (service) {
    return service.fetch(new Request(`https://gridflow-control-api.internal${path}`, init));
  }

  const controlApiUrl = process.env.CONTROL_API_URL;
  if (!controlApiUrl) {
    throw new Error("Live control API is not configured.");
  }
  return fetch(`${controlApiUrl.replace(/\/$/, "")}${path}`, init);
}

async function controlApiService(): Promise<ControlApiService | undefined> {
  try {
    const { env } = await getCloudflareContext({ async: true });
    return (env as CloudflareEnv & { CONTROL_API?: ControlApiService }).CONTROL_API;
  } catch {
    // Next.js local development does not expose Cloudflare service bindings.
    return undefined;
  }
}
