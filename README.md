# Mailroom demo links

Static fictional newsletter pages opened by links in Mailroom's demo inbox.

The product display name is set once in `build.py` as `APP_NAME`. Change that
value and rebuild to switch names (for example, from `Mailroom` to `Mailroom`)
without changing the repository name or public URL.

The published site is `https://mz8i.com/mailroom-demo/`. GitHub Pages should publish from the `docs/` directory on `main`.

## Build

With this repository beside the `digest` repository:

```powershell
python build.py
```

The build reads Mailroom's hand-written demo source and regenerates `docs/`. It uses only Python's standard library.

## Publish

Create a GitHub repository named `mailroom-demo`, push this repository to it, then configure Pages to deploy from the `main` branch's `/docs` folder. The existing `mz8i.com` Pages setup should expose the project at `https://mz8i.com/mailroom-demo/`.

Everything on the site is fictional demo content. The site uses no analytics, cookies, forms, external scripts, or remote images.
