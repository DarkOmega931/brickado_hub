from django.contrib import admin
from .models import LoyaltyEvent, Reward, RewardRedemption

@admin.register(LoyaltyEvent)
class LoyaltyEventAdmin(admin.ModelAdmin):
    list_display = ("user", "tipo", "pontos", "descricao", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("user__username", "descricao")

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("nome", "custo_pontos", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)

@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "pontos_usados", "criado_em", "concluido")
    list_filter = ("concluido", "criado_em")
    search_fields = ("user__username", "reward__nome")
