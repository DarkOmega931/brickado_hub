from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import LoyaltyEvent, Reward, RewardRedemption

@login_required
def loyalty_overview(request):
    eventos = LoyaltyEvent.objects.filter(user=request.user).order_by("-criado_em")
    total_eventos = (
        eventos.aggregate(total=Sum("pontos"))["total"] or 0
    )
    total_resgates = (
        RewardRedemption.objects.filter(user=request.user, concluido=True)
        .aggregate(total=Sum("pontos_usados"))["total"]
        or 0
    )
    pontos = total_eventos - total_resgates

    rewards = Reward.objects.filter(ativo=True).order_by("custo_pontos")[:4]

    context = {
        "pontos": pontos,
        "eventos": eventos,
        "rewards": rewards,
    }
    return render(request, "loyalty/loyalty_overview.html", context)

@login_required
def reward_list(request):
    eventos = LoyaltyEvent.objects.filter(user=request.user)
    total_eventos = (
        eventos.aggregate(total=Sum("pontos"))["total"] or 0
    )
    total_resgates = (
        RewardRedemption.objects.filter(user=request.user, concluido=True)
        .aggregate(total=Sum("pontos_usados"))["total"]
        or 0
    )
    pontos = total_eventos - total_resgates

    rewards = Reward.objects.filter(ativo=True).order_by("custo_pontos")

    if request.method == "POST":
        reward_id = request.POST.get("reward_id")
        reward = get_object_or_404(Reward, id=reward_id)
        if pontos >= reward.custo_pontos:
            RewardRedemption.objects.create(
                user=request.user,
                reward=reward,
                pontos_usados=reward.custo_pontos,
                concluido=True,
            )
            LoyaltyEvent.objects.create(
                user=request.user,
                tipo=LoyaltyEvent.BONUS,
                pontos=-reward.custo_pontos,
                descricao=f"Resgate de recompensa: {reward.nome}",
            )
            return redirect("loyalty_overview")

    return render(
        request,
        "loyalty/reward_list.html",
        {"pontos": pontos, "rewards": rewards},
    )
