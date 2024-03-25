from django.http import JsonResponse
import json
from django.shortcuts import render
from .models import Greeting

# Create your views here.

# def index(request):
#    context = {'message': 'Hello, Django! I am learning to make changes.'}
#    return render(request, "index.html", context)


CTL_SCORES_FILE_PATH = 'ctl_scores.json'

def index(request):
    try:
        with open(CTL_SCORES_FILE_PATH, 'r') as file:
            ctl_scores = json.load(file)
            return JsonResponse(ctl_scores, safe=False)  
    except FileNotFoundError:
        # If the file is not found, return an error message as JSON
        return JsonResponse({'error': 'CTL scores file not found.'}, status=404)


# other options: Not working :(
'''
from utils.functions import fetch_sessions_tss, calculate_ctl_atl_tsb

def index(request):
    user_id = 14  
    
    # Fetch TSS data dynamically
    df_tss = fetch_sessions_tss(user_id)
    
    # Calculate CTL, ATL, TSB scores
    df_scores = calculate_ctl_atl_tsb(df_tss)
    
    # OPTION A: For JSON Response
    return JsonResponse(df_scores.to_dict(orient='records'), safe=False)
    
    # OPTION B: ...
'''



def db(request):
    # If you encounter errors visiting the `/db/` page on the example app, check that:
    #
    # When running the app on Heroku:
    #   1. You have added the Postgres database to your app.
    #   2. You have uncommented the `psycopg` dependency in `requirements.txt`, and the `release`
    #      process entry in `Procfile`, git committed your changes and re-deployed the app.
    #
    # When running the app locally:
    #   1. You have run `./manage.py migrate` to create the `hello_greeting` database table.

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})


