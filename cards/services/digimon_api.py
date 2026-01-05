# cards/services/digimon_api.py
import time
import requests
from dataclasses import dataclass
from typing import Optional

from django.core.cache import cache
from django.utils import timezone

from cards.models import DigimonCard

BASE_SEARCH = "https://digimoncard.io/api-public/search"

# =========================
# Configurações do cache
# =========================
API_MIN_INTERVAL_SECONDS = 1.2  # segura: ~1 chamada a cada 1.2s (ajuste)
CARD_STALE_DAYS = 30            # só atualiza se dados estiverem "velhos"
CACHE_RATE_KEY = "digimon_api_last_call_ts"

@dataclass
class ApiResult:
    ok: bool
    error: str = ""
    payload: Optional[dict] = None

def _rate_limit_wait():
    """
    Garante um intervalo mínimo entre chamadas (por processo).
    Use cache do Django pra compartilhar entre requests.
    """
    last_ts = cache.get(CACHE_RATE_KEY)
    now_ts = time.time()

    if last_ts is not None:
        elapsed = now_ts - float(last_ts)
        if elapsed < API_MIN_INTERVAL_SECONDS:
            time.sleep(API_MIN_INTERVAL_SECONDS - elapsed)

    cache.set(CACHE_RATE_KEY, time.time(), timeout=60)

def _fetch_by_cardnumber(cardnumber: str) -> ApiResult:
    try:
        _rate_limit_wait()

        r = requests.get(BASE_SEARCH, params={"card": cardnumber}, timeout=15)
        r.raise_for_status()
        data = r.json()

        if not data:
            return ApiResult(ok=False, error="Carta não encontrada na API.", payload=None)

        return ApiResult(ok=True, payload=data[0])
    except requests.exceptions.HTTPError as e:
        # 429 costuma ser rate limit
        status = getattr(e.response, "status_code", None)
        if status == 429:
            return ApiResult(ok=False, error="Limite de requests da API atingido (429). Tente novamente em instantes.")
        return ApiResult(ok=False, error=f"Erro HTTP na API: {status or ''}".strip())
    except Exception as e:
        return ApiResult(ok=False, error=f"Falha ao consultar API: {e}")

def _to_int(v):
    try:
        if v is None or v == "":
            return None
        return int(v)
    except Exception:
        return None

def _safe_str(v):
    return (v or "").strip()

def upsert_card_from_api(cardnumber: str) -> ApiResult:
    """
    Busca um card pela API e salva/atualiza no DigimonCard.
    Retorna ApiResult com payload e/ou erro.
    """
    cardnumber = _safe_str(cardnumber)
    if not cardnumber:
        return ApiResult(ok=False, error="Cardnumber vazio.")

    res = _fetch_by_cardnumber(cardnumber)
    if not res.ok:
        return res

    p = res.payload or {}

    obj, _created = DigimonCard.objects.update_or_create(
        cardnumber=cardnumber,
        defaults={
            "name": _safe_str(p.get("name")),
            "card_type": _safe_str(p.get("type") or p.get("cardtype")),
            "color": _safe_str(p.get("color")),
            "level": _to_int(p.get("level")),
            "dp": _to_int(p.get("dp")),
            "play_cost": _to_int(p.get("play_cost") or p.get("playcost")),
            "evo_cost_1": _to_int(p.get("evo_cost") or p.get("evocost")),
            "evo_color_1": _safe_str(p.get("evo_color") or p.get("evocolor")),
            "attribute": _safe_str(p.get("attribute")),
            "digitype": _safe_str(p.get("digitype")),
            "rarity": _safe_str(p.get("rarity")),
            "pack": _safe_str(p.get("pack")),
            "effect": _safe_str(p.get("effect")),
            "inherit_effect": _safe_str(p.get("inherit_effect") or p.get("inheriteffect")),
            "security_effect": _safe_str(p.get("security_effect") or p.get("securityeffect")),
            "image_url": _safe_str(p.get("image_url") or p.get("image")),
            "last_synced_at": timezone.now(),
        },
    )

    return ApiResult(ok=True, payload={"saved": True, "cardnumber": obj.cardnumber})

def get_or_fetch_card(cardnumber: str, allow_refresh: bool = False) -> ApiResult:
    """
    Primeiro tenta pegar do banco.
    Se não existir, busca na API e salva.
    Se existir e allow_refresh=True, atualiza só se estiver stale.
    """
    cardnumber = _safe_str(cardnumber)
    if not cardnumber:
        return ApiResult(ok=False, error="Cardnumber vazio.")

    obj = DigimonCard.objects.filter(cardnumber=cardnumber).first()
    if obj:
        if allow_refresh and obj.last_synced_at:
            age_days = (timezone.now() - obj.last_synced_at).days
            if age_days >= CARD_STALE_DAYS:
                return upsert_card_from_api(cardnumber)
        return ApiResult(ok=True, payload={"from_db": True, "cardnumber": obj.cardnumber})

    # não existe no banco => chama API e salva
    return upsert_card_from_api(cardnumber)
