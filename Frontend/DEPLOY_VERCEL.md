Deploying this frontend to Vercel

1. Ensure you have a working build locally:

```
npm install
npm run build
```

2. From the project root, deploy with Vercel CLI or connect the repo in Vercel dashboard.

- With Vercel CLI:
```
npm i -g vercel
vercel login
vercel --prod
```

Vercel will run the `vercel-build` script (configured to run `npm run build`) and serve the `dist/client` folder as a static site.

Notes:
- This configuration deploys the client build only (static assets from `dist/client`). If you need SSR or the Node server in `dist/server`, add a serverless API wrapper or switch to a custom platform that supports the full server bundle.
