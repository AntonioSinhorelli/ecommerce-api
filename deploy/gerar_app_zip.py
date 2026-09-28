"""
Gera deploy/app.zip para upload no Elastic Beanstalk (arquivos na RAIZ do zip).
Uso (na raiz do projeto):  python deploy/gerar_app_zip.py
"""
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'deploy' / 'app.zip'

INCLUIR = ['manage.py', 'requirements.txt', 'Procfile', 'runtime.txt', '.ebextensions', 'ecommerce', 'vendas']
IGNORAR = {'__pycache__', '.env', 'db.sqlite3', 'staticfiles', '.git', '.venv', 'venv'}

with zipfile.ZipFile(DESTINO, 'w', zipfile.ZIP_DEFLATED) as zf:
    for item in INCLUIR:
        caminho = RAIZ / item
        arquivos = [caminho] if caminho.is_file() else sorted(caminho.rglob('*'))
        for arq in arquivos:
            if arq.is_file() and not (set(arq.relative_to(RAIZ).parts) & IGNORAR) and arq.suffix != '.pyc':
                # usa "/" como separador (zip gerado no Windows com "\" quebra no Linux do EB)
                zf.write(arq, arq.relative_to(RAIZ).as_posix())

print(f'Gerado: {DESTINO}')
