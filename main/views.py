from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect, render
from main import analysis


# Create your views here.
def index(request):
    marker = 1
    if request.method == 'POST':
        analysis.handle_uploaded_file(request.FILES.getlist('file_upload'))
        marker = 15
    elif request.method == 'GET':
        marker = 22
    return render(request, 'main/index.html', {'values': analysis.results, 'non_cleared': marker})


def about(request):
    return render(request, 'main/about.html')

