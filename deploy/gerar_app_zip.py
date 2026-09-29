"""
Gera deploy/app.zip para upload no Elastic Beanstalk (arquivos na RAIZ do zip).
Uso (na raiz do projeto):  python deploy/gerar_app_zip.py
"""
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'deploy' / 'app.zip'

INCLUIR = ['manage.py', 'requirements.txt', 'Procfile', 'runtime.txt', '.ebextensions', '.platform', 'ecommerce', 'vendas']
IGNORAR = {'__pycache__', '.env', 'db.sqlite3', 'staticfiles', 'static', '.git', '.venv', 'venv'}

with zipfile.ZipFile(DESTINO, 'w', zipfile.ZIP_DEFLATED) as zf:
    for item in INCLUIR:
        caminho = RAIZ / item
        arquivos = [caminho] if caminho.is_file() else sorted(caminho.rglob('*'))
        for arq in arquivos:
            if arq.is_file() and not (set(arq.relative_to(RAIZ).parts) & IGNORAR) and arq.suffix != '.pyc':
                # usa "/" como separador (zip gerado no Windows com "\" quebra no Linux do EB)
                nome = arq.relative_to(RAIZ).as_posix()
                if arq.suffix == '.sh':
                    # scripts de hook precisam ser executáveis e com fim de linha Unix (LF)
                    info = zipfile.ZipInfo(nome)
                    info.external_attr = 0o100755 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    zf.writestr(info, arq.read_bytes().replace(b'\r\n', b'\n'))
                else:
                    zf.write(arq, nome)

print(f'Gerado: {DESTINO}')
