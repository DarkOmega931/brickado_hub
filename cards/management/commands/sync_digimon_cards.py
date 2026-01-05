import csv
import time
import requests

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from cards.models import DigimonCard

API_URL = "https://digimoncard.io/api-public/search"


def to_int(v):
    try:
        if v is None or v == "":
            return None
        return int(v)
    except Exception:
        return None


class Command(BaseCommand):
    help = "Sync manual das cartas Digimon: lê cardnumbers de um seed e atualiza o cache local (DigimonCard)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", required=True, help="Arquivo .txt ou .csv com cardnumbers")
        parser.add_argument("--sleep", type=float, default=0.35, help="Delay entre requests (segundos)")
        parser.add_argument("--limit", type=int, default=0, help="Processa só N cardnumbers (0=sem limite)")
        parser.add_argument("--only-missing", action="store_true", help="Sincroniza apenas cartas que ainda não existem")
        parser.add_argument("--update-existing", action="store_true", help="Atualiza também as já existentes (default: sim)")
        parser.add_argument("--dry-run", action="store_true", help="Não grava no banco (só simula)")

    def handle(self, *args, **opts):
        seed_path = opts["seed"]
        sleep_s = opts["sleep"]
        limit = opts["limit"]
        only_missing = opts["only-missing"]
        dry_run = opts["dry-run"]

        # por padrão: atualiza existentes
        update_existing = opts["update-existing"] or True

        # lê seed
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                raw = f.read().splitlines()
        except FileNotFoundError:
            raise CommandError(f"Seed não encontrado: {seed_path}")

        cardnumbers = []
        for ln in raw:
            ln = (ln or "").strip()
            if not ln:
                continue
            # se for csv simples "BT4-016,algo" pega a 1ª coluna
            cn = ln.split(",")[0].strip()
            if cn and cn not in cardnumbers:
                cardnumbers.append(cn)

        if not cardnumbers:
            raise CommandError("Seed vazio. Coloque 1 cardnumber por linha (ex: BT4-016).")

        if limit and limit > 0:
            cardnumbers = cardnumbers[:limit]

        created = updated = skipped = failed = 0

        self.stdout.write(self.style.WARNING(f"SYNC MANUAL: {len(cardnumbers)} cardnumbers (sleep={sleep_s}s)"))

        for i, cn in enumerate(cardnumbers, start=1):
            try:
                exists = DigimonCard.objects.filter(cardnumber=cn).exists()
                if only_missing and exists:
                    skipped += 1
                    self.stdout.write(f"[{i}] {cn}: já existe (skip)")
                    continue

                # chama API APENAS no sync manual
                r = requests.get(API_URL, params={"card": cn}, timeout=25)
                r.raise_for_status()
                data = r.json()

                if not data:
                    failed += 1
                    self.stdout.write(self.style.ERROR(f"[{i}] {cn}: sem retorno"))
                    time.sleep(sleep_s)
                    continue

                c = data[0]

                defaults = {
                    "name": (c.get("name") or "").strip(),
                    "card_type": (c.get("type") or c.get("card_type") or "").strip(),
                    "color": (c.get("color") or "").strip(),
                    "level": to_int(c.get("level")),
                    "dp": to_int(c.get("dp")),
                    "play_cost": to_int(c.get("play_cost") or c.get("cost")),
                    "evo_cost_1": to_int(c.get("evolution_cost") or c.get("evocost") or c.get("evo_cost")),
                    "evo_color_1": (c.get("evolution_color") or c.get("evocolor") or "").strip(),
                    "attribute": (c.get("attribute") or "").strip(),
                    "digitype": (c.get("digitype") or c.get("digi_type") or "").strip(),
                    "rarity": (c.get("rarity") or "").strip(),
                    "pack": (c.get("pack") or "").strip(),
                    "effect": (c.get("effect") or "").strip(),
                    "inherit_effect": (c.get("inherit_effect") or c.get("inheritable_effect") or "").strip(),
                    "security_effect": (c.get("security_effect") or "").strip(),
                    "image_url": (c.get("image_url") or "").strip(),
                    "last_synced_at": timezone.now(),
                }

                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"[{i}] {cn}: DRY-RUN ok"))
                    time.sleep(sleep_s)
                    continue

                if exists and not update_existing:
                    skipped += 1
                    self.stdout.write(f"[{i}] {cn}: existe (não atualiza)")
                    time.sleep(sleep_s)
                    continue

                obj, was_created = DigimonCard.objects.update_or_create(
                    cardnumber=cn,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"[{i}] {cn}: criado"))
                else:
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f"[{i}] {cn}: atualizado"))

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"[{i}] {cn}: erro -> {e}"))

            time.sleep(sleep_s)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Fim do sync: {created} criados, {updated} atualizados, {skipped} ignorados, {failed} falharam."
        ))
