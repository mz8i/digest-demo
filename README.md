# Digest demo links

Static fictional newsletter pages opened by links in Digest's demo inbox.

The published site is `https://mz8i.com/digest-demo/`. GitHub Pages should publish from the `docs/` directory on `main`.

## Build

With this repository beside the `digest` repository:

```powershell
python build.py
```

The build reads Digest's hand-written demo source and regenerates `docs/`. It uses only Python's standard library.

## Publish

Create a GitHub repository named `digest-demo`, push this repository to it, then configure Pages to deploy from the `main` branch's `/docs` folder. The existing `mz8i.com` Pages setup should expose the project at `https://mz8i.com/digest-demo/`.

Everything on the site is fictional demo content. The site uses no analytics, cookies, forms, external scripts, or remote images.
