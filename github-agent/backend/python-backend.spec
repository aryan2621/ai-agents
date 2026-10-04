# -*- mode: python ; coding: utf-8 -*-
# Bundles the FastAPI backend into a folder (dist/python-backend/) that the app ships in Resources.
# Built by `npm run build:sidecar`. Keep this file in git: without it a fresh clone can't build the app.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = (
    collect_submodules("app")
    + collect_submodules("uvicorn")
    + collect_submodules("langgraph")
    + collect_submodules("langchain_openai")
    + collect_submodules("tiktoken_ext")
)
datas = collect_data_files("speech_recognition")
datas += [("../ports.json", ".")]  # read by app.config

a = Analysis(
    ["main.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
# A folder build (onedir), not one self-extracting file: a one-file build unpacks ~80 MB to a
# temp folder on every launch, which made the backend take 13-65 s to start instead of ~1 s.
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="python-backend",
    console=True,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="python-backend", upx=False)
