from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_google(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login_google.html')
