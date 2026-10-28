# Publishing watercolourmap to PyPI

This is a note for you, and it isn't included in the package. The built files are already in `dist/` and pass PyPI's checks.

## Before you publish

- **Licence.** The package uses MIT, which means anyone can use, change and sell work made with it, as long as they keep your copyright notice. If you'd rather not allow that, change `LICENSE` and the `license` line in `pyproject.toml` before uploading. Once a version is on PyPI, it can't be re-licensed.
- **Your private code stays private.** The package contains only the watercolour engine and the Urban Atlas poster tool. "Life on the go" and your own commands are not in it. The CLI no longer signs maps with @ET by default: pass `--signature "@ET" --website etymo.co.uk` for your own prints.

## Steps

1. Create an account at [pypi.org](https://pypi.org/account/register/), turn on two-factor authentication, and make an API token under Account settings → API tokens.
2. Optionally, test the upload first on [test.pypi.org](https://test.pypi.org). It needs a separate account and token.

   ```bash
   pip install twine
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple watercolourmap
   ```

3. Publish for real:

   ```bash
   twine upload dist/*
   ```

   When asked, the username is `__token__` and the password is your API token.

4. Check https://pypi.org/project/watercolourmap/ and try `pip install watercolourmap`.

## Releasing a new version later

Change `version` in `pyproject.toml` and `__version__` in `src/watercolourmap/__init__.py`, then run:

```bash
rm -rf dist && python -m build && twine check dist/* && twine upload dist/*
```

PyPI never accepts the same version number twice.

## Install locally without publishing

```bash
pip install watercolourmap-0.1.0-py3-none-any.whl
```
