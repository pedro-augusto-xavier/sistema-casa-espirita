"""Backup do banco com pg_dump.

Uso:
    python -m scripts.backup

Gera backups/casa_espirita_AAAAMMDD_HHMMSS.sql.gz (formato custom, comprimido).
Precisa do pg_dump no PATH (vem junto com o PostgreSQL).
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import settings

PASTA = Path("backups")


def main() -> None:
    url = make_url(settings.DATABASE_URL)
    PASTA.mkdir(exist_ok=True)

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = PASTA / f"{url.database}_{carimbo}.dump"

    comando = [
        "pg_dump",
        "-h", url.host or "localhost",
        "-p", str(url.port or 5432),
        "-U", url.username or "postgres",
        "-d", url.database or "",
        # formato custom: comprimido e restaurável com pg_restore
        "-F", "c",
        "-f", str(destino),
    ]

    ambiente = dict(os.environ)
    if url.password:
        ambiente["PGPASSWORD"] = url.password

    print("Rodando:", " ".join(comando))
    try:
        subprocess.run(comando, env=ambiente, check=True)
    except FileNotFoundError:
        sys.exit(
            "pg_dump não encontrado no PATH. Adicione a pasta bin do PostgreSQL "
            "(ex: D:\\PostGres\\bin) ao PATH e tente de novo."
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"pg_dump falhou (código {exc.returncode}).")

    tamanho_kb = destino.stat().st_size / 1024
    print(f"Backup salvo em {destino} ({tamanho_kb:.0f} KB)")
    print("Restaurar com: pg_restore -d NOME_DO_BANCO --clean --if-exists ARQUIVO")


if __name__ == "__main__":
    main()
