# Core library imports
import sys

# 3rd-party imports
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
#from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
#from rest_framework import viewsets
import environ
import json
import requests

# Local app imports
from . import infoget_classes
from .tokens import account_activation_token


# Load the .env
env = environ.Env()
env.read_env(sys.path[0] + '/redeyecore/.env')
#from .Models import LobServers



###########################################################################################


# New user registration
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():

            email_address = form.cleaned_data.get('username')

            # Check, must be a corporate email
            if '@mycompany.com' not in email_address:
                messages.error(request, 'Must be your company email address')
                form = UserCreationForm()
                return render(request, 'registration/register.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, email_address)
            return redirect('home')

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = UserCreationForm()

    return render(
        request=request,
        template_name="registration/register.html",
        context={"form": form}
        )



###########################################################################################


# Sends an email to a new user with a link to confirm their email address and complete their registration
def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Please go to your inbox for {to_email} and click on \
            the activation link to complete the registration. Note: Check your spam folder.')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


###########################################################################################


# When the new user clicks on the link in the confirmation email, this happens and the account is activated
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return HttpResponse('Thank you for your email confirmation. You can now <a href="/login">login</a> to your account.')
    else:
        return HttpResponse('Activation link is invalid!')



###########################################################################################


# Home page
def home(request):
    # Needfuls
    #from django.utils import timezone as djtimezone
    #import json
    #import requests

    # We don't actually need this yet
    # Activate time zone specified in settings.py
    from django.conf import settings
    from django.utils.timezone import activate
    activate(settings.TIME_ZONE)


    # New empty lists to hold info for home page display
    agents_with_redline_issues = []
    agents_with_kaseya_issues = []
    agents_totally_offline = []
    agents_missing_custom_field = []
    

    # Instantiate the 'mysql_database' class and connect to the app db
    # Get a cursor with a GLOBAL scope
    try:

        # Get the connection info from the .env as separate, individual strings
        app_db_host = env('app_db_host')
        app_db_username = env('app_db_username')
        app_db_password = env('app_db_password')
        app_db_database = env('app_db_database')

        # Connect to the database and get a cursor
        app_db_connect = infoget_classes.mysql_database(app_db_host, app_db_username, app_db_password, app_db_database)
        app_db_cursor = app_db_connect.get_cursor()

        # For error check in home.html
        app_db_connect_error = "App DB Connect OK"

    except Exception as e0:
        app_db_connect_error = 'Error: {}, sys.path: {}'.format(e0, sys.path[0])
        # Build the context
        context = {
            'app_db_connect_error': app_db_connect_error
        }

        # Return the result(s)
        return render(request, 'home.html', context)



    # Got a cursor, now get the existing auth token from the database via SELECT query
    app_db_cursor.reset()
    app_db_cursor.execute("SELECT MAX(app_run_number) FROM redshift.infoget_lobservers")
    app_run_number = str(app_db_cursor.fetchone()[0])


    # Get VSA agents missing the GCS Custom Fields
    # These need to have the GCS scripts run on them
    app_db_cursor.reset()
    cf_query_string = "SELECT rmm_agent_name, rmm_gcc_file_type, rmm_gcc_computer_name, rmm_last_checkin FROM redshift.infoget_lobservers WHERE app_run_number = {} AND ((rmm_gcc_file_type IS NULL OR rmm_gcc_file_type = '') OR (rmm_gcc_computer_name IS NULL OR rmm_gcc_computer_name = ''))".format(app_run_number)
    app_db_cursor.execute(cf_query_string)
    agents_with_custom_field_problems = app_db_cursor.fetchall()
    agents_missing_custom_field.append(agents_with_custom_field_problems)
    agents_missing_custom_field_count = len(agents_missing_custom_field[0])



    # Get LOB servers that are offline in Redline, but online in Kaseya
    # These need to have the AppService restarted and checked
    app_db_cursor.reset()
    cf_query_string = "SELECT rmm_agent_name, red_location, red_last_lob_query, red_last_lob_update  FROM redshift.infoget_lobservers WHERE app_run_number = {} AND (red_agent_is_offline = TRUE AND rmm_agent_is_offline = FALSE) ORDER BY red_last_lob_query ASC".format(app_run_number)
    app_db_cursor.execute(cf_query_string)
    redline_issues = app_db_cursor.fetchall()
    agents_with_redline_issues.append(redline_issues)
    agents_with_redline_issues_count = len(agents_with_redline_issues[0])



    # Get LOB servers that are offline in Kaseya, but online in Redline
    # These need to be rebooted by an FS
    app_db_cursor.reset()
    cf_query_string = "SELECT rmm_agent_name, red_location, rmm_last_checkin, red_last_lob_query  FROM redshift.infoget_lobservers WHERE app_run_number = {} AND (red_agent_is_offline = FALSE AND rmm_agent_is_offline = TRUE) ORDER BY rmm_last_checkin ASC".format(app_run_number)
    app_db_cursor.execute(cf_query_string)
    kaseya_issues = app_db_cursor.fetchall()
    agents_with_kaseya_issues.append(kaseya_issues)
    agents_with_kaseya_issues_count = len(agents_with_kaseya_issues[0])



    # Get LOB servers that are offline in Kaseya AND offline in Redline
    # These need to be investigated for ISP issues, etc
    app_db_cursor.reset()
    cf_query_string = "SELECT rmm_agent_name, red_location, rmm_last_checkin, red_last_lob_query  FROM redshift.infoget_lobservers WHERE app_run_number = {} AND (red_agent_is_offline = TRUE AND rmm_agent_is_offline = TRUE) ORDER BY rmm_last_checkin ASC".format(app_run_number)
    app_db_cursor.execute(cf_query_string)
    totally_offline = app_db_cursor.fetchall()
    agents_totally_offline.append(totally_offline)
    agents_totally_offline_count = len(agents_totally_offline[0])





    ########## THE BIG SHOW - PART 2: RETURN THE FINAL RESULT ##########
    # Build the context
    context = {
        'app_db_connect_error': app_db_connect_error,
        #'redline_db_connect_error': redline_db_connect_error,
        'app_run_number': app_run_number,
        'agents_missing_custom_field': agents_missing_custom_field,
        'agents_missing_custom_field_count': agents_missing_custom_field_count,
        'agents_with_redline_issues': agents_with_redline_issues,
        'agents_with_redline_issues_count': agents_with_redline_issues_count,
        'agents_with_kaseya_issues': agents_with_kaseya_issues,
        'agents_with_kaseya_issues_count': agents_with_kaseya_issues_count,
        'agents_totally_offline': agents_totally_offline,
        'agents_totally_offline_count': agents_totally_offline_count,
    }

    # Return the result(s)
    return render(request, 'home.html', context)



###########################################################################################


# About page
def about(request):
    return render(request, 'about.html', {})


###########################################################################################

# Other views
