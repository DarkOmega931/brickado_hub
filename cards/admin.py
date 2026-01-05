# cards/admin.py
import csv
import io
import time
import requests
from decimal import Decimal, InvalidOperation

from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.utils import timezone

from .models import (
    DigimonCard,
    CardPrice,
    CardCopyRule,
    BanlistRule,
    PairBanRule,
)

# =========================
# Helpers Sync
# =========================

def _to_int(v):
    try:
        if v is None or v == "":
            return None
        return int(v)
    except Exception:
        return None


def _safe_str(v) -> str:
    return (v or "").strip()


def _parse_seed_file(file_obj) -> list[str]:
    """
    Aceita:
    - TXT: 1 cardnumber por linha
    - CSV: se tiver coluna 'cardnumber' usa ela, senão usa 1ª coluna
    """
    raw = file_obj.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []

    first = lines[0]
    is_csv = ("," in first) or (";" in first) or ("\t" in first)

    if not is_csv:
        out = []
        for ln in lines:
            cn = ln.split()[0].strip().upper()
            if cn and cn not in out:
                out.append(cn)
        return out

    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
    except Exception:
        dialect = csv.excel
        dialect.delimiter = ","

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return []

    headers = [h.strip() for h in reader.fieldnames if h]
    lower_map = {h.lower(): h for h in headers}

    out = []
    if "cardnumber" in lower_map:
        key = lower_map["cardnumber"]
        for row in reader:
            cn = (row.get(key) or "").strip().upper()
            if cn and cn not in out:
                out.append(cn)
        return out

    first_col = headers[0]
    for row in reader:
        cn = (row.get(first_col) or "").strip().upper()
        if cn and cn not in out:
            out.append(cn)
    return out


def _sync_one_card(cardnumber: str, sleep_s: float = 0.25) -> tuple[bool, str]:
    """
    Sync unitário (API search por cardnumber) e salva no DigimonCard.
    """
    API_URL = "https://digimoncard.io/api-public/search"
    cn = (cardnumber or "").strip().upper()
    if not cn:
        return False, "cardnumber vazio"

    r = requests.get(API_URL, params={"card": cn}, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not data:
        return False, "API retornou vazio"

    c = data[0]

    defaults = {
        "name": _safe_str(c.get("name")),
        "card_type": _safe_str(c.get("type") or c.get("card_type")),
        "color": _safe_str(c.get("color")),
        "color2": _safe_str(c.get("color2")),
        "level": _to_int(c.get("level")),
        "dp": _to_int(c.get("dp")),
        "play_cost": _to_int(c.get("play_cost") or c.get("cost")),
        "evo_cost_1": _to_int(c.get("evolution_cost") or c.get("evocost") or c.get("evo_cost")),
        "evo_color_1": _safe_str(c.get("evolution_color") or c.get("evocolor")),
        "evo_level_1": _to_int(c.get("evolution_level") or c.get("evo_level")),
        "attribute": _safe_str(c.get("attribute")),
        "digitype": _safe_str(c.get("digitype") or c.get("digi_type")),
        "digitype2": _safe_str(c.get("digitype2") or c.get("digi_type2")),
        "form": _safe_str(c.get("form")),
        "rarity": _safe_str(c.get("rarity")),
        "pack": _safe_str(c.get("pack")),
        "effect": _safe_str(c.get("effect")),
        "inherit_effect": _safe_str(c.get("inherit_effect") or c.get("inheritable_effect")),
        "security_effect": _safe_str(c.get("security_effect")),
        "image_url": _safe_str(c.get("image_url")),
        "last_synced_at": timezone.now(),
    }

    DigimonCard.objects.update_or_create(
        cardnumber=cn,
        defaults=defaults,
    )

    if sleep_s:
        time.sleep(sleep_s)

    return True, "ok"


def _fetch_all_cardnumbers() -> list[str]:
    """
    Sync B: puxa lista completa (cardnumber + name) da API getAllCards.
    """
    url = "https://digimoncard.io/api-public/getAllCards"
    params = {
        "sort": "name",
        "series": "Digimon Card Game",
        "sortdirection": "asc",
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    out = []
    for item in data:
        cn = (item.get("cardnumber") or item.get("id") or "").strip().upper()
        if cn:
            out.append(cn)

    # remove duplicados mantendo ordem
    seen = set()
    uniq = []
    for cn in out:
        if cn not in seen:
            seen.add(cn)
            uniq.append(cn)
    return uniq


# =========================
# DigimonCard admin + Sync A/B dentro do ModelAdmin (sem patch global)
# =========================
@admin.register(DigimonCard)
class DigimonCardAdmin(admin.ModelAdmin):
    list_display = ("cardnumber", "name", "card_type", "color", "level", "dp", "last_synced_at")
    search_fields = ("cardnumber", "name", "card_type", "color", "digitype", "attribute", "pack", "rarity")
    list_filter = ("card_type", "color", "rarity")
    ordering = ("cardnumber",)

    # Para colocar botões no topo do changelist:
    change_list_template = "admin/cards/digimoncard_changelist.html"

    def get_urls(self):
        """
        REGISTRA urls no padrão que o template do admin espera:
        admin:cards_digimoncard_digimon_sync_a
        admin:cards_digimoncard_digimon_sync_b
        """
        urls = super().get_urls()
        custom = [
            path(
                "digimon-sync-a/",
                self.admin_site.admin_view(self.digimon_sync_a_view),
                name="cards_digimoncard_digimon_sync_a",
            ),
            path(
                "digimon-sync-a/template/",
                self.admin_site.admin_view(self.digimon_sync_a_template),
                name="cards_digimoncard_digimon_sync_a_template",
            ),
            path(
                "digimon-sync-b/",
                self.admin_site.admin_view(self.digimon_sync_b_view),
                name="cards_digimoncard_digimon_sync_b",
            ),
        ]
        return custom + urls

    def digimon_sync_a_template(self, request):
        resp = HttpResponse(content_type="text/plain; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="digimon_sync_seed_template.txt"'
        resp.write("BT4-016\nBT8-084\nBT13-112\n")
        return resp

    def digimon_sync_a_view(self, request):
        """
        Sync A: Seed (TXT/CSV) -> sync por cardnumber
        """
        if request.method == "POST":
            seed_file = request.FILES.get("seed_file")
            only_missing = request.POST.get("only_missing") == "on"
            sleep_raw = (request.POST.get("sleep_s") or "0.25").strip()

            try:
                sleep_s = float(sleep_raw)
                if sleep_s < 0:
                    sleep_s = 0.0
            except Exception:
                sleep_s = 0.25

            if not seed_file:
                messages.error(request, "Envie um arquivo seed (TXT/CSV).")
                return redirect("..")

            cardnumbers = _parse_seed_file(seed_file)
            if not cardnumbers:
                messages.error(request, "Não encontrei nenhum cardnumber no seed.")
                return redirect("..")

            created = 0
            updated = 0
            skipped = 0
            failed = 0

            for cn in cardnumbers:
                exists = DigimonCard.objects.filter(cardnumber__iexact=cn).exists()
                if only_missing and exists:
                    skipped += 1
                    continue

                try:
                    ok, msg = _sync_one_card(cn, sleep_s=sleep_s)
                    if ok:
                        if exists:
                            updated += 1
                        else:
                            created += 1
                    else:
                        failed += 1
                        messages.warning(request, f"{cn}: {msg}")
                except Exception as e:
                    failed += 1
                    messages.warning(request, f"{cn}: erro -> {e}")

            messages.success(
                request,
                f"Sync A concluído: {created} criados, {updated} atualizados, {skipped} ignorados, {failed} com erro."
            )
            return redirect("..")

        context = {
            **self.admin_site.each_context(request),
            "title": "Digimon Sync A (Seed)",
            "template_url_name": "admin:cards_digimoncard_digimon_sync_a_template",
        }
        return render(request, "admin/cards/digimon_sync_a.html", context)

    def digimon_sync_b_view(self, request):
        """
        Sync B: Full list -> pega TODOS cardnumbers e sincroniza.
        (Pode demorar. Use com cautela.)
        """
        if request.method == "POST":
            only_missing = request.POST.get("only_missing") == "on"
            sleep_raw = (request.POST.get("sleep_s") or "0.25").strip()
            limit_raw = (request.POST.get("limit") or "").strip()

            try:
                sleep_s = float(sleep_raw)
                if sleep_s < 0:
                    sleep_s = 0.0
            except Exception:
                sleep_s = 0.25

            limit = None
            if limit_raw:
                try:
                    limit = max(1, int(limit_raw))
                except Exception:
                    limit = None

            try:
                all_cards = _fetch_all_cardnumbers()
            except Exception as e:
                messages.error(request, f"Falha ao buscar lista completa (getAllCards): {e}")
                return redirect("..")

            if limit:
                all_cards = all_cards[:limit]

            created = 0
            updated = 0
            skipped = 0
            failed = 0

            for cn in all_cards:
                exists = DigimonCard.objects.filter(cardnumber__iexact=cn).exists()
                if only_missing and exists:
                    skipped += 1
                    continue

                try:
                    ok, msg = _sync_one_card(cn, sleep_s=sleep_s)
                    if ok:
                        if exists:
                            updated += 1
                        else:
                            created += 1
                    else:
                        failed += 1
                        messages.warning(request, f"{cn}: {msg}")
                except Exception as e:
                    failed += 1
                    messages.warning(request, f"{cn}: erro -> {e}")

            messages.success(
                request,
                f"Sync B concluído: {created} criados, {updated} atualizados, {skipped} ignorados, {failed} com erro."
            )
            return redirect("..")

        context = {
            **self.admin_site.each_context(request),
            "title": "Digimon Sync B (Full)",
        }
        return render(request, "admin/cards/digimon_sync_b.html", context)


# =========================
# CardPrice (preço por cardnumber) + Upload CSV + Template
# =========================
@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    list_display = ("cardnumber", "name", "price", "in_stock", "updated_at")
    search_fields = ("cardnumber", "name")
    list_filter = ("in_stock",)
    ordering = ("cardnumber",)

    change_list_template = "admin/cards/cardprice_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("upload-csv/", self.admin_site.admin_view(self.upload_csv), name="cards_cardprice_upload_csv"),
            path("download-template/", self.admin_site.admin_view(self.download_template), name="cards_cardprice_download_template"),
        ]
        return custom + urls

    def download_template(self, request):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="brickado_card_prices_template.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["cardnumber", "price", "name", "product_url", "in_stock"])
        writer.writerow(["BT4-016", "12.90", "Aldamon", "", "1"])
        writer.writerow(["BT8-084", "8.50", "MagnaGarurumon", "", "1"])
        writer.writerow(["BT13-112", "39.99", "Omnimon", "", "0"])
        return response

    def upload_csv(self, request):
        if request.method == "POST":
            f = request.FILES.get("csv_file")
            if not f:
                messages.error(request, "Selecione um arquivo CSV.")
                return redirect("..")

            if not f.name.lower().endswith(".csv"):
                messages.error(request, "O arquivo precisa ser .csv")
                return redirect("..")

            try:
                raw = f.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    raw = f.read().decode("latin-1")
                except Exception:
                    messages.error(request, "Não consegui ler o CSV. Salve como UTF-8 e tente novamente.")
                    return redirect("..")

            sample = raw[:2048]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
            except Exception:
                dialect = csv.excel
                dialect.delimiter = ","

            reader = csv.DictReader(io.StringIO(raw), dialect=dialect)
            if not reader.fieldnames:
                messages.error(request, "CSV inválido: cabeçalho não encontrado.")
                return redirect("..")

            headers = [h.strip() for h in reader.fieldnames if h]
            lower_map = {h.lower(): h for h in headers}

            required = {"cardnumber", "price"}
            if not required.issubset(lower_map.keys()):
                messages.error(request, "CSV inválido. Cabeçalhos obrigatórios: cardnumber, price")
                return redirect("..")

            created = 0
            updated = 0
            skipped = 0
            errors = []

            for idx, row in enumerate(reader, start=2):
                cardnumber = (row.get(lower_map["cardnumber"]) or "").strip().upper()
                raw_price = (row.get(lower_map["price"]) or "").strip()

                if not cardnumber or not raw_price:
                    skipped += 1
                    continue

                raw_price = raw_price.replace("R$", "").strip()
                if raw_price.count(","):
                    raw_price = raw_price.replace(".", "").replace(",", ".")
                else:
                    raw_price = raw_price.replace(",", ".")

                try:
                    price = Decimal(raw_price)
                    if price < 0:
                        raise InvalidOperation()
                except (InvalidOperation, ValueError):
                    errors.append(f"Linha {idx}: preço inválido '{row.get(lower_map['price'])}' para {cardnumber}")
                    continue

                name = (row.get(lower_map.get("name", ""), "") or "").strip()
                product_url = (row.get(lower_map.get("product_url", ""), "") or "").strip()

                in_stock = True
                if "in_stock" in lower_map:
                    stock_raw = (row.get(lower_map["in_stock"]) or "").strip().lower()
                    if stock_raw in ("0", "false", "nao", "não", "n", "no"):
                        in_stock = False

                _, was_created = CardPrice.objects.update_or_create(
                    cardnumber=cardnumber,
                    defaults={
                        "price": price,
                        "name": name,
                        "product_url": product_url,
                        "in_stock": in_stock,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

            if errors:
                for e in errors[:8]:
                    messages.warning(request, e)
                if len(errors) > 8:
                    messages.warning(request, f"... e mais {len(errors) - 8} erro(s).")

            messages.success(
                request,
                f"Upload concluído: {created} criado(s), {updated} atualizado(s), {skipped} ignorado(s)."
            )
            return redirect("..")

        context = {
            **self.admin_site.each_context(request),
            "title": "Upload em lote de preços (CSV)",
        }
        return render(request, "admin/cards/cardprice_upload.html", context)


# =========================
# Regras: exceções de cópias / banlist / pair-ban
# =========================
@admin.register(CardCopyRule)
class CardCopyRuleAdmin(admin.ModelAdmin):
    list_display = ("cardnumber", "max_copies", "notes")
    search_fields = ("cardnumber", "notes")
    ordering = ("cardnumber",)


@admin.register(BanlistRule)
class BanlistRuleAdmin(admin.ModelAdmin):
    list_display = ("cardnumber", "status", "notes")
    list_filter = ("status",)
    search_fields = ("cardnumber", "notes")
    ordering = ("cardnumber",)


@admin.register(PairBanRule)
class PairBanRuleAdmin(admin.ModelAdmin):
    list_display = ("card_a", "card_b", "notes")
    search_fields = ("card_a", "card_b", "notes")
    ordering = ("card_a", "card_b")
# =========================