from django.http import HttpResponse

def home(request):
    return HttpResponse("HOME VIEW OK - VERSAO TESTE")
