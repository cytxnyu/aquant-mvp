# GitHub Workflow

## MCP Status In This Session

The GitHub MCP tools available in this session can inspect the authenticated user and search/read repository metadata. They do not expose fork, clone, create-repository, push or pull-request write operations in the current tool list.

Checked account:

- GitHub login: `cytxnyu`
- Profile: `https://github.com/cytxnyu`

Reference searches were done through MCP for:

- `microsoft/qlib`
- `akfamily/akshare`

No external repository code was copied into this project.

## Initialize This Project As A Git Repository

From the workspace root:

```powershell
git init
git add .
git commit -m "Initial A-share quant research platform"
```

## Create A GitHub Repository Manually

Create an empty repository on GitHub, for example:

```text
https://github.com/cytxnyu/aquant-mvp
```

Then connect and push:

```powershell
git branch -M main
git remote add origin https://github.com/cytxnyu/aquant-mvp.git
git push -u origin main
```

## Clone Later

```powershell
git clone https://github.com/cytxnyu/aquant-mvp.git
cd aquant-mvp
python -m pip install -e .[dev]
python run_mvp.py run-demo
python -m pytest
```

## Optional External References

If you want to clone reference projects for local reading, keep them outside the main package tree:

```powershell
New-Item -ItemType Directory -Force external
git clone https://github.com/microsoft/qlib.git external/qlib
git clone https://github.com/akfamily/akshare.git external/akshare
```

Do not copy reference project code into `src/aquant_mvp` unless you have reviewed and complied with the upstream license.

