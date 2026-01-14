from pathlib import Path
import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from decks.models import Archetype


class Command(BaseCommand):
    help = (
        "Importa arquétipos a partir de um arquivo CSV ou TXT.\n\n"
        "Formato aceito:\n"
        "- TXT: um arquétipo por linha\n"
        "- CSV: primeira coluna = nome, segunda coluna opcional = slug\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "filepath",
            type=str,
            help="Caminho do arquivo CSV ou TXT com os arquétipos",
        )
        parser.add_argument(
            "--delimiter",
            default=";",
            help="Delimitador do CSV (padrão: ';')",
        )
        parser.add_argument(
            "--has-header",
            action="store_true",
            help="Indique se o CSV possui linha de cabeçalho",
        )

    def handle(self, *args, **options):
        filepath = Path(options["filepath"])
        delimiter = options["delimiter"]
        has_header = options["has_header"]

        if not filepath.exists():
            raise CommandError(f"Arquivo não encontrado: {filepath}")

        suffix = filepath.suffix.lower()
        self.stdout.write(self.style.NOTICE(f"Importando arquétipos de {filepath}..."))

        if suffix in {".csv", ".tsv"}:
            created, updated = self._import_csv(filepath, delimiter, has_header)
        else:
            created, updated = self._import_txt(filepath)

        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída. Criados: {created}, Atualizados: {updated}."
        ))

    # ---------- Importadores ----------

    def _import_txt(self, filepath: Path):
        created = 0
        updated = 0

        with filepath.open(encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if not name:
                    continue

                slug = slugify(name)
                obj, is_created = Archetype.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name},
                )
                if is_created:
                    created += 1
                else:
                    # se já existir, atualiza o nome caso tenha mudado
                    if obj.name != name:
                        obj.name = name
                        obj.save(update_fields=["name"])
                        updated += 1

        return created, updated

    def _import_csv(self, filepath: Path, delimiter: str, has_header: bool):
        created = 0
        updated = 0

        with filepath.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)

            if has_header:
                next(reader, None)  # pula cabeçalho

            for row in reader:
                if not row:
                    continue

                name = (row[0] or "").strip()
                if not name:
                    continue

                if len(row) > 1 and row[1].strip():
                    slug = row[1].strip()
                else:
                    slug = slugify(name)

                obj, is_created = Archetype.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name},
                )
                if is_created:
                    created += 1
                else:
                    if obj.name != name:
                        obj.name = name
                        obj.save(update_fields=["name"])
                        updated += 1

        return created, updated
