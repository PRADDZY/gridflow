# GridFlow Control Room

The operator and signage surfaces for GridFlow's race-day queue-safety workflow.

The UI deliberately treats analytics as decision support. A person must approve
every steward assignment and sign update; no model output takes action by itself.

## Local development

```powershell
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3000` for the operator board and
`http://localhost:3000/display` for the public signage view.

## Cloudflare deployment

This package uses [OpenNext for Cloudflare](https://opennext.js.org/cloudflare).

```powershell
npm.cmd run preview
npm.cmd run deploy
```

Before the first deployment, configure the `gridflow-control-room` Worker in
`wrangler.jsonc` with the appropriate Cloudflare account and bindings. Runtime
secrets stay in Cloudflare, never in this repository.

## Demo media

The evidence frame references a freely usable demo video still from
[Pexels](https://www.pexels.com/video/queue-of-people-in-urban-setting-during-daytime-35253208/).
Production deployments replace it with the venue's approved CCTV gateway.
