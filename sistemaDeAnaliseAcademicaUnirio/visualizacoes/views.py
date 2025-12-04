from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
import os
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go

USER_ID = 'user1'


# Upload de arquivos

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)

CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')

def ensure_user_dirs():
    os.makedirs(USER_DIR, exist_ok=True)
    os.makedirs(CURRICULOS_DIR, exist_ok=True)



