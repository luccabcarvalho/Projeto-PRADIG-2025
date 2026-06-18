from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def progresso(request):
    return render(request, 'progresso.html')