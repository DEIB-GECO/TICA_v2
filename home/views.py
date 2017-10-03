from django.shortcuts import render

# Create your views here.


def index(request):
    greeting_message = "This is a mock main page for TICA v2 site. " \
              "Hello Arif, I changed the code! =)"
    context = {
        'message': greeting_message,
    }
    return render(request, 'home/index.html', context)