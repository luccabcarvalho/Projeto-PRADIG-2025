from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def migracao(request):
    return render(request, 'migracao.html')