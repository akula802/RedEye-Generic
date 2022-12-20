# Core library and/or django imports
from django.apps import AppConfig
#import sys

# 3rd-party imports
from apscheduler.schedulers.background import BackgroundScheduler

# Local app imports
#sys.path.append("..")
from . import jobs

############################


class InfogetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infoget'

    def ready(self):
        #import logging

        # Start logging
        #logging.getLogger('apscheduler').setLevel(logging.INFO)

        # Prevents the ready() method from running twice on server start
        # https://stackoverflow.com/a/67973819
        import os
        run_once = os.environ.get('INFOGET_RUN_ONCE') 
        if run_once is not None:
            return
        os.environ['INFOGET_RUN_ONCE'] = 'True' 

	# Added 9/20 to try and stop this ready() method from running multiples
	# https://stackoverflow.com/a/52430581
	#if os.environ.get('RUN_MAIN', None) != 'true':

        # Create the scheduler object
        scheduler = BackgroundScheduler(timezone='America/Denver')
        scheduler.add_job(jobs.get_vsa_and_lobapp_data, 'interval', minutes=30, replace_existing=True)

        # Check for existing instance, don't start another if present
        if not scheduler.running: 
            scheduler.start()




