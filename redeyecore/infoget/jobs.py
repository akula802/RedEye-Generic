# Core library and/or django imports
import logging
from logging.handlers import RotatingFileHandler
import sys

# 3rd-party imports
import environ

# Local app imports
from . import infoget_classes

# Load the .env
env = environ.Env()
env.read_env(sys.path[0] + '/redeyecore/.env')


############################


# Configure logging 
logging.basicConfig(
    #filename='infoget_job.log',  #commented out on 10/14/2022 for core-002(b)

    # Attempt at log rotation by max size
    handlers=[RotatingFileHandler('./infoget_job.log', maxBytes=100000, backupCount=10)],
    level=logging.INFO,
    format='%(asctime)s: %(levelname)s: File %(filename)s | Function %(funcName)s | Line %(lineno)d: %(message)s'
    )

logging.getLogger('apscheduler').setLevel(logging.INFO)


############################


def get_vsa_and_lobapp_data():

    # Logging
    logging.debug('Function triggered as job.')

    # Core library imports
    import json
    import requests

    # New empty list to store the final INSERT items
    # This will be a list of dicts, with keys = column names in the 'infoget_lobservers' table
    final_combined_data_to_insert = []

    # New empty list to hold gate agents missing the custom fields
    agents_missing_custom_field = []

    # VSA API URL to get ALL gate agents (all agents in the 'gate' group)
    vsa_all_gate_agents_url = "https://realserverurl.kaseya.net/API/v1.0/assetmgmt/agents?$filter=substringof('gate', MachineGroup)"


    ##### BEGIN MYSQL APP DB CONNECT #####
    # Instantiate the 'mysql_database' class and connect to the app db
    # Get a cursor with a GLOBAL scope
    try:
        logging.debug("Connecting to APP database...")

        # Get the connection info from the .env as separate, individual strings
        app_db_host = env('app_db_host')
        app_db_username = env('app_db_username')
        app_db_password = env('app_db_password')
        app_db_database = env('app_db_database')

        # Connect to the app db and get a cursor
        app_db_connect = infoget_classes.mysql_database(app_db_host, app_db_username, app_db_password, app_db_database)
        app_db_cursor = app_db_connect.get_cursor()
        logging.debug("Finished commands to connect to APP database.")

        # For error check in home.html
        app_db_connect_error = "App DB Connect OK"
        logging.info('APP database connection result: {}'.format(app_db_connect_error))

    except Exception as e0:
        app_db_connect_error = e0
        return app_db_connect_error
        logging.critical('APP database connection failed: {}'.format(app_db_connect_error))
        #exit()


    # Got a cursor, now get the existing auth token from the database via SELECT query
    app_db_cursor.reset()
    app_db_cursor.execute("SELECT vsa_auth_token FROM infoget_vsaauthtokens")
    existing_token = str(app_db_cursor.fetchone()[0])
    #logging.info('Existing token= {}'.format(existing_token))  # Leave this commented out, useful for testing/debugging only

    # Now get the app_rmm_fetch_time
    app_db_cursor.reset()
    app_db_cursor.execute("SELECT NOW()")
    app_rmm_fetch_time = str(app_db_cursor.fetchone()[0])
    ##### END MYSQL APP DB CONNECT #####




    ##### BEGIN LOB APP DB CONNECT #####
    # Instantiate the 'postgres_database' class and connect to LOB App
    # Get a cursor with a GLOBAL scope, for use later
    try:
        logging.debug("Connecting to LOB App database...")

        # Get the connection info from .env
        lobapp_db_host = env('lobapp_db_host')
        lobapp_db_port = env('lobapp_db_port')
        lobapp_db_username = env('lobapp_db_username')
        lobapp_db_password = env('lobapp_db_password')
        lobapp_db_database = env('lobapp_db_database')

        # Connect to the LOB APP database and get a cursor
        lobapp_db_connect = infoget_classes.postgres_database(lobapp_db_host, lobapp_db_port, lobapp_db_username, lobapp_db_password, lobapp_db_database)
        lobapp_db_cursor = lobapp_db_connect.get_cursor(lobapp_db_connect)
        logging.debug("Finished commands to connect to LOB App database.")

        # For error check in home.html
        lobapp_db_connect_error = "LOB app DB Connect OK"
        lobapp_test_query_result = lobapp_db_cursor
        logging.info('LOB App database connection result: {}'.format(lobapp_db_connect_error))


    except Exception as e1:
        lobapp_db_connect_error = e1
        logging.critical('LOB App database connection failed: {}'.format(lobapp_db_connect_error))
        #exit()


    # Set the app_lob_fetch_time by selecting current time from LOB App
    app_lob_fetch_time_query = "SELECT CURRENT_TIMESTAMP(0)::TIMESTAMP WITHOUT TIME ZONE"
    lobapp_db_cursor.execute(app_lob_fetch_time_query)
    app_lob_fetch_time_utc = lobapp_db_cursor.fetchall()
    # Convert the time to mysql
    for item in app_lob_fetch_time_utc:
        app_lob_fetch_time_object = infoget_classes.time_convert(item[0])
        app_lob_fetch_time = app_lob_fetch_time_object.lobapp_to_mysql()
    ##### END LOB APP DB CONNECT #####




    # Make the first VSA call using the existing token
    # If it fails, the class method will get a new token and update the database

    ### VSA - ALL GATE AGENTS ###
    # Instantiate the vsa api request class and get ALL gate agents
    vsa_all_gate_agents_request_object = infoget_classes.make_vsa_api_request(vsa_all_gate_agents_url, existing_token)
    vsa_all_gate_agents_result = vsa_all_gate_agents_request_object.request_result_all()
    vsa_all_gate_agents = vsa_all_gate_agents_result[1]
    logging.info("Executed 'vsa_all_gate_agents' call. Got HTTP {}".format(vsa_all_gate_agents_result[0]))



    # Reset the 'existing_token' object now that we've run our first query 
    app_db_cursor.reset()
    app_db_cursor.execute("SELECT vsa_auth_token FROM infoget_vsaauthtokens")
    existing_token = str(app_db_cursor.fetchone()[0])






    # Loop through 'vsa_all_gate_agents' and add relevant values to 'data_for_insert' dict
    logging.info("Starting the 'for agent in vsa_all_gate_agents' loop.")
    for agent in vsa_all_gate_agents[1]:

        try:
            # Create a new empty dict
            data_for_insert = {
                'app_run_number': '',
                'app_rmm_fetch_time': '',
                'app_lob_fetch_time': '',
                'rmm_agent_id': '',
                'lob_computer_name': '',
                'rmm_lac_computer_name': '',
                'rmm_computer_name': '',
                'rmm_agent_name': '',
                'lob_location': '',
                'rmm_lac_file_type': '',
                'rmm_last_reboot': '',
                'rmm_last_checkin': '',
                'lob_last_gate_update': '',
                'lob_last_gate_query': '',
                'rmm_ram_mbytes': '',
                'rmm_cpu_type': '',
                'rmm_agent_is_offline': '',
                'lob_agent_is_offline': '',
                'rmm_uptime_score': '',
                'lob_uptime_score': ''
                }


            # Start pulling data for the insert
            # The queries below don't follow the order of the dict items above

            # Get the 'app_run_number' from the database
            app_db_cursor.reset()
            app_db_cursor.execute("SELECT MAX(app_run_number) FROM redeye.infoget_lobservers")

            # Increment the run number for this run
            old_app_run_number = str(app_db_cursor.fetchone()[0])
            app_run_number = int(old_app_run_number) + 1
            data_for_insert['app_run_number'] = app_run_number


            # Set the timestamps
            data_for_insert['app_rmm_fetch_time'] = app_rmm_fetch_time
            data_for_insert['app_lob_fetch_time'] = app_lob_fetch_time


            # Get the Kaseya agent ID
            data_for_insert['rmm_agent_id'] = agent['AgentId']


            # Get the 'lac-DeviceName' Custom Field for the agent
            # Get the VSA Custom Field called 'LAC-DeviceName' that ties the agents to the LOB app 'lob_app_computers' table
            custom_field_query_url = 'https://realserverurl.kaseya.net/API/v1.0/assetmgmt/assets/{}/customfields'.format(agent['AgentId'])
            custom_field_request_object = infoget_classes.make_vsa_api_request(custom_field_query_url, existing_token)
            custom_field_request_result = custom_field_request_object.request_result_all()
            custom_field = custom_field_request_result[1]
            # logging.debug("Finished getting 'custom_field' for {}".format(agent['AgentName']))

            # Added for 'issue-001'
            #if not isinstance(custom_field, list):
                # Do something?

            # Another test for 'issue-001'
            if '__iter__' not in  dir(custom_field):
                # convert it to a list I guess?
                custom_field = list(custom_field)


            # Define the possible FileTypes in rmm_lac_file_type
            file_types = ['Vendor1', 'Vendor2', 'Vendor3', 'Vendor4', 'Vendor5', 'Vendor6', 'Vendor7']

            if len(custom_field[1]['Result']) > 1:
                # Get the rmm_lac_computer_name
                # Depends on the '_' character being present in the LAC-DeviceName Custom Field
                for field_value in custom_field[1]['Result']:
                    if '_' in field_value['FieldValue']:
                    # if 'rd' in field_value['FieldValue']:  # better way then checking for '_'?
                        data_for_insert['rmm_lac_computer_name'] = field_value['FieldValue']
                        vsa_lac_device_name = field_value['FieldValue']


                # Get the rmm_lac_file_type
                for file_type in file_types:
                    for field_value in custom_field[1]['Result']:
                            if file_type in field_value['FieldValue']:
                                    data_for_insert['rmm_lac_file_type'] = file_type



            # Custom Field does not exist, could be a problem agent, keep track here
            else:
                agents_missing_custom_field.append([agent['ComputerName'], agent['AgentId'], agent['AgentName']])
                # logging.debug("{} is missing custom fields.".format(agent['AgentName']))
                # Set vsa_lac_device_name to None (issue-002)
                vsa_lac_device_name = ''
                data_for_insert['rmm_lac_computer_name'] = None
                data_for_insert['rmm_lac_file_type'] = None




            data_for_insert['rmm_computer_name'] = agent['ComputerName']
            data_for_insert['rmm_agent_name'] = agent['AgentName']

            # Now that we have the Custom Field data, use it to query the LOB app database
            # Get this agent's facility ID (site_code) from LOB app
            # Issue-002: Check for blank vsa_lac_device_name first, in case the custom fields are missing/blank
            if not vsa_lac_device_name:
                data_for_insert['lob_location'] = None
            else:
                lob_site_query = "SELECT f.site_code FROM lob_app_computers lac INNER JOIN facilities f ON f.id=lac.facility_id WHERE lac.device_name = \'{}\'".format(vsa_lac_device_name)
                lob_db_cursor.execute(lobapp_site_query)
                lob_location = lobapp_db_cursor.fetchall()
                # Append the LOB app site data to the insert dict for this agent
                # The loop is necessary because stupidity
                for item in lob_location:
                    data_for_insert['lob_location'] = item[0]


            # Get this agent's device_name from LOB app
            # issue-002: Check for blank vsa_lac_device_name first, in case the custom fields are missing/blank
            if not vsa_lac_device_name:
                data_for_insert['lob_computer_name'] = None
            else:
                lobapp_site_query = "SELECT lac.device_name FROM lob_app_computers lac WHERE lac.device_name = \'{}\'".format(vsa_lac_device_name)
                lobapp_db_cursor.execute(lobapp_site_query)
                lob_computer_name = lobapp_db_cursor.fetchall()
                # Append the LOB app site data to the insert dict for this agent
                for item in lob_computer_name:
                    data_for_insert['lob_computer_name'] = item[0]


            ####### 'lob_last_gate_query'
            # Get this agent's last query timestamp from LOB app
            # Issue-002: Check for blank vsa_lac_device_name first, in case the custom fields are missing / blank
            if not vsa_lac_device_name:
                data_for_insert['lob_last_gate_query'] = None
            else:
                lobapp_last_queried_query = "SELECT CASE WHEN lac.last_queried IS NULL THEN '1000-01-01 00:00:00' ELSE lac.last_queried END FROM lob_app_computers lac WHERE lac.device_name = \'{}\'".format(vsa_lac_device_name)
                lobapp_db_cursor.execute(lobapp_last_queried_query)
                lob_last_gate_query_utc = lobapp_db_cursor.fetchall()

                for item in lob_last_gate_query_utc:
                    # Instantiate the time_convert class
                    lob_last_query_convert_object = infoget_classes.time_convert(item[0])
                    lob_last_gate_query_raw = lob_last_query_convert_object.lobapp_to_mysql()

                    # Check for database-side NULL values
                    if '1000-01-01 00:00:00' in lob_last_gate_query_raw:
                        lob_last_gate_query = None
                    else:
                        lob_last_gate_query = lob_last_gate_query_raw

                    # Append the LOB app site data to the insert dict for this agent
                    data_for_insert['lob_last_gate_query'] = lob_last_gate_query



            ####### 'lob_last_gate_update'
            # Get this agent's last gate code update (file download) timestamp from LOB app
            # Issue-002: Check for blank vsa_lac_device_name first, in case the custom fields are missing / blank
            # Issue-005 this was polling lac.last_queried instead of lac.last_checked
            if not vsa_lac_device_name:
                data_for_insert['lob_last_gate_update'] = None
            else:
                lobapp_last_gate_update_query = "SELECT CASE WHEN lac.last_checked IS NULL THEN '1000-01-01 00:00:00' ELSE lac.last_checked END FROM lob_app_computers lac WHERE lob.device_name = \'{}\'".format(vsa_lob_device_name)
                lobapp_db_cursor.execute(lobapp_last_gate_update_query)
                lobapp_last_gate_update_utc = lobapp_db_cursor.fetchall()

                for item in LOB app_last_gate_update_utc:
                    # Instantiate the time_convert class
                    lob_last_update_convert_object = infoget_classes.time_convert(item[0])
                    lob_last_gate_update_raw = lob_last_update_convert_object LOB app_to_mysql()

                    # Check for database-side NULL values
                    if '1000-01-01 00:00:00' in lob_last_gate_update_raw:
                        lob_last_gate_update = None
                    else:
                        lob_last_gate_update = lob_last_gate_update_raw

                    # Append the LOB app site data to the insert dict for this agent
                    data_for_insert['lob_last_gate_update'] = lob_last_gate_update



            # 'lob_agent_is_offline'
            # Issue-002: Check for blank vsa_lob_device_name first, in case the custom fields are missing / blank
            if not vsa_lob_device_name:
                data_for_insert['lob_agent_is_offline'] = True
            else:
                if '1000-01-01 00:00:00' in lob_last_gate_update_raw or '1000-01-01 00:00:00' in lob_last_gate_query_raw:
                    lob_agent_is_offline = True

                # Added this smarter check on 10/17/2022 for feature-007
                else:
                    # Needfuls
                    from datetime import datetime

                    # Get current timestamp and convert the lob_last_gate_query string back into a datetime object
                    now = datetime.utcnow()
                    lobts_dt = datetime.strptime(lob_last_gate_query, '%Y-%m-%d %H:%M:%S')

                    # Get the difference between now and lob_last_gate_query, in seconds
                    difference = (now - lobts_dt).total_seconds()

                    # 10 minutes = (10*60) = 600 seconds
                    # If no AppService checkin for 10+ minutes, it's to be considered offline
                    if difference >= 600:
                        lob_agent_is_offline = True
                    else:
                        lob_agent_is_offline = False


                # Add the result to the final insert dict
                data_for_insert['lob_agent_is_offline'] = lob_agent_is_offline



            # Convert the VSA LastRebootTime field to MySQL timestamp
            rmm_last_reboot_object = infoget_classes.time_convert(agent['LastRebootTime'])
            rmm_last_reboot = rmm_last_reboot_object.vsa_to_mysql()
            # Check for database-side NULL values
            if '1000-01-01 00:00:00' in rmm_last_reboot:
                data_for_insert['rmm_last_reboot'] = None
            else:
                data_for_insert['rmm_last_reboot'] = rmm_last_reboot


            # Convert the VSA LastCheckInTime field to MySQL timestamp
            rmm_last_checkin_object = infoget_classes.time_convert(agent['LastCheckInTime'])
            rmm_last_checkin = rmm_last_checkin_object.vsa_to_mysql()
            # Check for database-side NULL values
            if '1000-01-01 00:00:00' in rmm_last_checkin:
                data_for_insert['rmm_last_checkin'] = None
            else:
                data_for_insert['rmm_last_checkin'] = rmm_last_checkin

            # Get the agent's RAM and CPU type from VSA
            data_for_insert['rmm_ram_mbytes'] = agent['RamMBytes']
            data_for_insert['rmm_cpu_type'] = agent['CpuType']

            # Get the VSA online status flag
            if agent['Online'] == 0:
                rmm_agent_is_offline = True
            else:
                rmm_agent_is_offline = False
            data_for_insert['rmm_agent_is_offline'] = rmm_agent_is_offline



            ########## feature-013 ##########

            # get the uptime scores for Kaseya and LOB app
            uptime_scores = []
            uptime_agent_id = agent['AgentId']

            uptime_score_query_string = """
            SELECT

                ROUND(((SELECT COUNT(*)
                FROM infoget_lobservers
                WHERE rmm_agent_id = '{0}'
                AND rmm_agent_is_offline = False
                AND app_run_number IS NOT NULL
                AND app_run_number <> ''
                AND app_run_number <> 0)
                / (SELECT COUNT(*)
                FROM infoget_lobservers
                WHERE rmm_agent_id = '{0}'
                AND app_run_number IS NOT NULL
                AND app_run_number <> ''
                AND app_run_number <> 0) * 100), 2) AS rmm_uptime_score,

                ROUND(((SELECT COUNT(*) FROM infoget_lobservers
                WHERE rmm_agent_id = '{0}'
                AND lob_agent_is_offline = False
                AND app_run_number IS NOT NULL
                AND app_run_number <> ''
                AND app_run_number <> 0)
                / (SELECT COUNT(*)
                FROM infoget_lobservers
                WHERE rmm_agent_id = '{0}'
                AND app_run_number IS NOT NULL
                AND app_run_number <> ''
                AND app_run_number <> 0) * 100), 2) AS lob_uptime_score

                FROM redeye.infoget_lobservers igs

                WHERE igs.rmm_agent_id = '{0}'
                AND igs.app_run_number = (SELECT MAX(app_run_number) FROM redeye.infoget_lobservers)

                """.format(uptime_agent_id)

            try:
                app_db_cursor.reset()
                app_db_cursor.execute(uptime_score_query_string)
                uptime_scores_result = app_db_cursor.fetchone()

                if uptime_scores_result is not None:
                    for item in uptime_scores_result:
                        uptime_scores.append(float(str(item)))
                        # RESULT is a list of floats: [99.63, 99.63]
                else:
                    # Just add zeroes
                    uptime_scores.append(0)
                    uptime_scores.append(0)


            except Exception as e99:
                # Again, just add zeroes, but also log
                uptime_scores.append(0)
                uptime_scores.append(0)
                uptime_score_fail_message = "Couldn't get uptime uptime_scores for {}: {}".format(agent['rmm_agent_name'], e99)
                logging.error(uptime_score_fail_message)

            # Add the uptime scores to the Insert dict
            data_for_insert['rmm_uptime_score'] = uptime_scores[0]
            data_for_insert['lob_uptime_score'] = uptime_scores[1]

            ########## feature-013 ##########



            # Finally, insert this dict into the final list
            final_combined_data_to_insert.append(data_for_insert)


        except Exception as e:
            fail_message = "Failed to run CustomField loop for agent ({}): {}, {}".format(agent['AgentID'], e, custom_field)
            final_combined_data_to_insert.append(fail_message)
            logging.critical(fail_message)
            #exit()


    logging.info("Finished running the data aggreagtion loop")



    ########## THE BIG SHOW: GET THE STUFF INTO THE DATABASE ##########

    # Count of items == number of rows that will be inserted
    # There are 17 columns, because 17 {key:value} pairs in each final_combined_data_to_insert item
    insert_items_count = len(final_combined_data_to_insert)


    # Loop through final_combined_data_to_insert
    try:

        # Clear out the API database, since it will only ever serve the most recent data
        #app_db_cursor.reset()
        query_string_0 = "DELETE FROM api_gateservers"
        app_db_cursor.execute(query_string_0)

        # Loop the rest of the results
        #app_db_cursor.reset()
        for row in final_combined_data_to_insert:

            ### CONSTRUCT THE SQL QUERIES

            # Build the main INSERT query as a string
            query_string_1 = "INSERT INTO infoget_lobservers (app_rmm_fetch_time, app_lob_fetch_time, rmm_agent_id, lob_computer_name, rmm_lac_computer_name, rmm_computer_name, rmm_agent_name, lob_location, rmm_lac_file_type, rmm_last_reboot, rmm_last_checkin, lob_last_gate_update, lob_last_gate_query, rmm_ram_mbytes, rmm_cpu_type, rmm_agent_is_offline, lob_agent_is_offline, app_run_number, rmm_uptime_score, lob_uptime_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            # Build the query to INSERT the data into the API database
            query_string_3 = "INSERT INTO api_gateservers (app_rmm_fetch_time, app_lob_fetch_time, rmm_agent_id, lob_computer_name, rmm_lac_computer_name, rmm_computer_name, rmm_agent_name, lob_location, rmm_lac_file_type, rmm_last_reboot, rmm_last_checkin, lob_last_gate_update, lob_last_gate_query, rmm_ram_mbytes, rmm_cpu_type, rmm_agent_is_offline, lob_agent_is_offline, app_run_number, rmm_uptime_score, lob_uptime_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"



            ### EXECUTE THE SQL QUERIES

            # Execute the main INSERT query
            app_db_cursor.execute(query_string_1, (row['app_rmm_fetch_time'], row['app_lob_fetch_time'], row['rmm_agent_id'], row['lob_computer_name'], row['rmm_lac_computer_name'], row['rmm_computer_name'], row['rmm_agent_name'], row['lob_location'], row['rmm_lac_file_type'], row['rmm_last_reboot'], row['rmm_last_checkin'], row['lob_last_gate_update'], row['lob_last_gate_query'], row['rmm_ram_mbytes'], row['rmm_cpu_type'], row['rmm_agent_is_offline'], row['lob_agent_is_offline'], row['app_run_number'], row['rmm_uptime_score'], row['lob_uptime_score']))

            # Execute the API database insert query
            app_db_cursor.execute(query_string_3, (row['app_rmm_fetch_time'], row['app_lob_fetch_time'], row['rmm_agent_id'], row['lob_computer_name'], row['rmm_lac_computer_name'], row['rmm_computer_name'], row['rmm_agent_name'], row['lob_location'], row['rmm_lac_file_type'], row['rmm_last_reboot'], row['rmm_last_checkin'], row['lob_last_gate_update'], row['lob_last_gate_query'], row['rmm_ram_mbytes'], row['rmm_cpu_type'], row['rmm_agent_is_offline'], row['lob_agent_is_offline'], row['app_run_number'], row['rmm_uptime_score'], row['lob_uptime_score']))



        # Commit and close
        app_db_connect.commit()
        app_db_connect.close()

        # Set insert_result for reporting and error checking
        insert_result = "Successfully inserted the aggregated data."
        logging.info(insert_result)
        #exit()



    except Exception as e:
        insert_result = "Failed to INSERT at {}: {}".format(row, e)
        logging.critical(insert_result)
        #exit()


