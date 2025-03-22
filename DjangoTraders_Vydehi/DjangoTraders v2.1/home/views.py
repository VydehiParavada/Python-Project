from django.shortcuts import render

# from django.http import HttpResponse

from datetime import datetime
from django.contrib.auth.decorators import login_required

"""
    The Views.py file defines "end points" - urls 
    such as "localhost:8000/home" or "localhost:8000/authorized"
"""


def home(request):
    """
    'home' is the name of the function thats mapped in urls.py
    This creates the home page for the "home" app we have created.
    """
    return render(
        # The return value contains 3 parts:
        # 1. "request" is the name (just a repeat of the original HttpRequest)
        # that the function is responding to
        request,
        # 2. template_name is the name of the template
        # used to return the HttpResonse back to the browser.
        # This is typically an html file in the Templates folder.
        "home/welcome.html",
        # The context or the data that is actually returned to the page
        # The context is a dictionary of key-value pairs
        #   Key - the name of the variable
        #   Value - the value of the "key" variable
        # For example, we are passing today with a formatting date, and
        # "time" with a value of the unformatted "today()" - as is.
        {
            "today": datetime.today().strftime("%A, %d. %B %Y"),
            "time": datetime.today().strftime("%H: %M"),
        },
    )


@login_required
def authorized(request):
    """
    The decorated function stipulates a condition
    that must be met for the content to be rendered.
    This is condition makes the function available to authorized users only.
    """
    return render(
        request,
        "home/authorized.html",
        {"today": datetime.today().strftime("%A, %d. %B %Y")},
    )
