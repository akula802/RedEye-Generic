# Classes for re-use

# Core library and/or django imports
import sys

# 3rd-party imports
import environ

# Local app imports

# Load the .env
env = environ.Env()
env.read_env(sys.path[0] + '/redeyecore/.env')


############################


class mysql_database:
    # Self init
    def __init__(self, db_host, db_user, db_passwd, db_database):
        self.db_host = db_host
        self.db_user = db_user
        self.db_passwd = db_passwd
        self.db_database = db_database


    # Function to connect to the databse and return a cursor object
    #def get_cursor(self, appdb):
    def get_cursor(self):

        try:
            # Needfuls
            import mysql.connector

            # Database connection info
            self.mysql_db = mysql.connector.connect(
                host = self.db_host,
                user = self.db_user,
                passwd = self.db_passwd,
                database = self.db_database,
            )
    
            # Create the cursor object
            self.mysql_db_cursor = self.mysql_db.cursor(buffered=True)

        # Exception encountered
        except Exception as bad_mysql_db_connect_attempt:
            final_result = "Database connection error: {}".format(bad_mysql_db_connect_attempt)
            return final_result

        # All good
        final_result = self.mysql_db_cursor
        return final_result


    # For the connection commit action
    def commit(self):
        self.mysql_db.commit()


    # For the connection close action
    def close(self):
        self.mysql_db.close()



##########################


class postgres_database:
    # Self init
    def __init__(self, db_host, db_port, db_user, db_passwd, db_database):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_passwd = db_passwd
        self.db_database = db_database


    # Function to connect to the databse and return a cursor object
    def get_cursor(self, postgres_db):

        try:
            # Needfuls
            import psycopg2

            # Database connection info
            self.postgres_db = psycopg2.connect(
                host = self.db_host,
                port = self.db_port,
                user = self.db_user,
                password = self.db_passwd,
                database = self.db_database,
            )
    
            # Create the cursor object
            self.postgres_db_cursor = self.postgres_db.cursor()

        # Exception encountered
        except Exception as bad_postgres_db_connect_attempt:
            final_result = "Database connection error: {}".format(bad_postgres_db_connect_attempt)
            return final_result

        # All good
        return self.postgres_db_cursor
        #final_result = self.postgres_db_cursor
        #return final_result



    #def execute(self):
    #    self.postgres_db_cursor.execute()


    # For the connection commit action
    def commit(self):
        self.postgres_db.commit()


    # For the connection close action
    def close(self):
        self.postgres_db.close()


##########################


class vsa_auth:
    # Self init
    def __init__(self, vsa_auth_url, vsa_username, vsa_user_token):
        self.vsa_auth_url = vsa_auth_url
        self.vsa_username = vsa_username
        self.vsa_user_token = vsa_user_token


    # Method to generate a new VSA auth token
    def get_vsa_auth_token(self):
        # Import the needfuls
        import requests
        import json

        # Make the auth call
        try:
            vsa_auth_response = requests.get(self.vsa_auth_url, auth=requests.auth.HTTPBasicAuth(username=self.vsa_username, password=self.vsa_user_token))

        except:
            fail_result = "Weirdness at initial auth request (1.1). HTTP Response: {} - {}".format(response.status_code, response.reason)
            return fail_result


        # Seems like the auth call worked, check response code
        if vsa_auth_response.status_code == 200:

            # Got 200, great, now load the json and get the token
            vsa_auth_response_json = json.loads(vsa_auth_response.content)
            vsa_new_auth_token = vsa_auth_response_json['Result']['Token']

            # Connect to the app database
            try:
                # Get the app db connection info from the .env as separate, individual strings
                app_db_host = env('app_db_host')
                app_db_username = env('app_db_username')
                app_db_password = env('app_db_password')
                app_db_database = env('app_db_database')


                # Instantiate the mysql_database class and connect to the app database
                db_connect = mysql_database(app_db_host, app_db_username, app_db_password, app_db_database)

                # Get a cursor
                cursor = db_connect.get_cursor()

            except:
                fail_result = "Failure on database connect (1.2)"
                return fail_result


            # Write the new auth token to the database
            try:
                # Make a list of lists for the values to insert
                # It has to be done this way to prevent SQL injection??
                # Can't just do string formatting
                values = [
                    [vsa_new_auth_token],
                ]

                replace_query = "UPDATE infoget_vsaauthtokens SET vsa_auth_token=%s, vsa_auth_token_timestamp=NOW() WHERE vsa_auth_token_timestamp < DATE_SUB(NOW(), INTERVAL 10 SECOND);"

                # Loop and do the insert
                cursor.reset()
                for value in values:
                    cursor.execute(replace_query, value)
                
                # Commit and close
                db_connect.commit()
                db_connect.close()

                # Return the new token
                return vsa_new_auth_token


            except Exception as e3:
                fail_result = "Failure on database INSERT (1.3): {}".format(e3)
                return fail_result


        else:
            fail_result = "Weirdness at initial auth request (1.4). Verify your user token, etc. HTTP Response: {} - {}".format(response.status_code, response.reason)
            return fail_result



##########################



class make_vsa_api_request:
    def __init__(self, request_url, bearer_token):
        self.request_url = request_url
        self.bearer_token = bearer_token


    def request_result_all(self):
        # Needfuls
        import requests
        import json
        import math


        # Final list to be returned if query is successful
        vsa_response_final = []

        # Initial query parameters
        header = {'Authorization': 'Bearer {}'.format(self.bearer_token)}

        # Make the initial query
        try:
            vsa_response = requests.get(self.request_url, headers=header)

        except Exception as e:
            fail_message = "Failed to make initial request (1.1). Got HTTP response: {}".format(vsa_response.status_code)
            return (fail_message, e)

        # Now check the HTTP status code
        #Some requests (e.g. Custom Fields) return '0' on success in the result content
        if vsa_response.status_code == 200:
            # Get the count and make a full query
            # Get the TotalRecords count, if applicable
            try:
                total_records_json = vsa_response.json()
                total_records = total_records_json['TotalRecords']
                vsa_response_final.append({'TotalRecords': total_records})
            except Exception as e:
                # There may not be a TotalRecord object, but the request got a 200 response
                # This is typical for simple requests that query by AgentID and return a single result
                # So no pagination is needed
                
                vsa_response_json = vsa_response.json()
                vsa_response_final.append({'TotalRecords': 1})
                vsa_response_final.append(vsa_response_json)

                # Return the data
                return (vsa_response.status_code, vsa_response_final)


            # TotalRecords should be an int, problem if not
            if isinstance(total_records, int) == True:

                # Divide total_records by 100, then round up to get number of pages / loop iterations needed
                total_pages = math.ceil(total_records / 100)

                # Do the looping
                iteration_counter = 0
                while iteration_counter < (total_pages):

                    # Build the 'skip' and 'top' parameters
                    top = 100

                    if iteration_counter > 0:
                        skip = iteration_counter * 100
                    else:
                        skip = 0

                    # Check request_url for '?'
                    try:
                        if '?' in self.request_url:
                            if 'skip' not in self.request_url and 'top' not in self.request_url:
                                added_param = '&$skip={}&$top={}'.format(skip, top)
                                temp_url = self.request_url + added_param
                                # Make the call
                                vsa_response2 = requests.get(temp_url, headers=header)
                                vsa_response2_json = vsa_response2.json()

                            else:
                                fail_result = "Failed: You can't use top or skip in base URLs for VSA (1.3)"
                                return fail_result

                        # Check request_url for '&'
                        elif '?' not in self.request_url:
                            if 'skip' not in self.request_url and 'top' not in self.request_url:
                                added_param = '?$skip={}&$top={}'.format(skip, top)
                                temp_url = self.request_url + added_param
                                # Make the call
                                vsa_response2 = requests.get(temp_url, headers=header)
                                vsa_response2_json = vsa_response2.json()

                            else:
                                fail_result = "Failed: You can't use top or skip in base URLs for VSA (1.4)"
                                return fail_result

                    except Exception as e:
                        fail_message = "Failed in pagination loop sequence (1.5)"
                        return (e, fail_message)


                    # Add to final_result list
                    # vsa_response_final.append(vsa_response2_json['Result'])
                    # iteration_counter += 1

                    if iteration_counter == 0:
                        vsa_response_final.append(vsa_response2_json['Result'])
                    else:
                        for agent in vsa_response2_json['Result']:
                            vsa_response_final[1].append(agent)

                    iteration_counter += 1

                # Now out of the while loop
                # Return the data
                return (vsa_response.status_code, vsa_response_final)

            # TotalRecords is not an int, wtf
            # You should never see this, but you're welcome, it's handled
            else:
                fail_result = "Failed: TotalRecords did not return an int object (1.6)."
                return fail_result



        # Got a 401, unauthorized
        elif vsa_response.status_code == 401:
            # Get a new bearer token
            # get VSA API connection info from .env
            vsa_username = env('vsa_auth_username')
            vsa_user_token = env('vsa_auth_user_token')
            auth_url = env('vsa_auth_url')

            # Instantiate the auth class
            auth_object = vsa_auth(auth_url, vsa_username, vsa_user_token)
            # Check for errors here

            # Get a new auth token
            try:
                new_auth_token = auth_object.get_vsa_auth_token()

                # The returned item should NOT contain '.' character unless there's an error message
                if '.' in new_auth_token:
                    fail_result = "Failed to get new auth token (1.7): {}".format(new_auth_token)
                    return (new_auth_token, fail_result)

            except Exception as e:
                fail_result = "Failed to instantiate auth_object (1.8)."
                return (e, fail_result)


            # Got the new auth token, run it all again
            try:
                new_header = {'Authorization': 'Bearer {}'.format(new_auth_token)}
                vsa_response = requests.get(self.request_url, headers=new_header)

            except Exception as e:
                fail_message = "Failed to make initial request (1.9). Got HTTP response: {}".format(vsa_response.status_code)
                return (fail_message, e)

            # Get the TotalRecords count
            try:
                total_records_json = vsa_response.json()
                total_records = total_records_json['TotalRecords']
                vsa_response_final.append({'TotalRecords': total_records})
                #total_records = vsa_response
            except Exception as e:
                # There may not be a TotalRecord object, but the request got a 200 response
                # This is typical for simple requests that query by AgentID and return a single result
                # So no pagination is needed
                
                vsa_response_json = vsa_response.json()
                vsa_response_final.append({'TotalRecords': 1})
                vsa_response_final.append(vsa_response_json)

                # Return the data
                return (vsa_response.status_code, vsa_response_final)


            # TotalRecords should be an int, problem if not
            if isinstance(total_records, int) == True:

                # Divide total_records by 100, then round up to get number of pages / loop iterations needed
                total_pages = math.ceil(total_records / 100)

                # Do the looping
                iteration_counter = 0
                while iteration_counter < (total_pages):

                    # Build the 'skip' and 'top' parameters
                    top = 100

                    if iteration_counter > 0:
                        skip = iteration_counter * 100
                    else:
                        skip = 0

                    # Check request_url for '?'
                    try:
                        if '?' in self.request_url:
                            if 'skip' not in self.request_url and 'top' not in self.request_url:
                                added_param = '&$skip={}&$top={}'.format(skip, top)
                                temp_url = self.request_url + added_param
                                # Make the call
                                vsa_response2 = requests.get(temp_url, headers=new_header)
                                vsa_response2_json = vsa_response2.json()

                            else:
                                fail_result = "Failed: You can't use top or skip in base URLs for VSA (1.11)"
                                return fail_result

                        # Check request_url for '&'
                        elif '?' not in self.request_url:
                            if 'skip' not in self.request_url and 'top' not in self.request_url:
                                added_param = '?$skip={}&$top={}'.format(skip, top)
                                temp_url = self.request_url + added_param
                                # Make the call
                                vsa_response2 = requests.get(temp_url, headers=new_header)
                                vsa_response2_json = vsa_response2.json()

                            else:
                                fail_result = "Failed: You can't use top or skip in base URLs for VSA (1.12)"
                                return fail_result

                    except Exception as e:
                        fail_message = "Failed in pagination loop sequence (1.13)"
                        return (e, fail_message)


                    # Add to final_result list
                    # vsa_response_final.append(vsa_response2_json['Result'])
                    # iteration_counter += 1

                    if iteration_counter == 0:
                        vsa_response_final.append(vsa_response2_json['Result'])
                    else:
                        for agent in vsa_response2_json['Result']:
                            vsa_response_final[1].append(agent)
                            
                    iteration_counter += 1

                # Now out of the while loop
                # Return the data
                return (vsa_response.status_code, vsa_response_final)

            # TotalRecords is not an int, wtf
            # You should never see this, but you're welcome, it's handled
            else:
                fail_result = "Failed: TotalRecords did not return an int object (1.14)."
                return fail_result


        # Didn't get a 200 or a 401, so wtf
        else:
            fail_message = "Failed to parse initial request (1.15). Got HTTP response: {}".format(vsa_response.status_code)
            return (vsa_response.status_code, fail_message)



##########################


class time_convert:
    def __init__(self, timestamp_string):
        self.timestamp_string = timestamp_string

    # MySQL datetime format is 'YYYY-MM-DD HH:MM:SS'
    # https://dev.mysql.com/doc/refman/8.0/en/datetime.html


    # For VSA to MySQL
    def vsa_to_mysql(self):
        # VSA format: 2022-08-06T16:42:49.033
        # VSA times are UTC

        # Core and/or django library imports
        from django.utils import timezone as djtimezone
        from datetime import datetime, timezone
        import time

        # 3rd-Party Imports
        import pytz

        # Handle the empty timestamp_string
        if not self.timestamp_string or '1000-01-01 00:00:00' in self.timestamp_string:
            vsa_fmtd_timestamp_local_str_final = '1000-01-01 00:00:00'
            return vsa_fmtd_timestamp_local_str_final

        # Make sure a string was supplied
        if isinstance(self.timestamp_string, str) == False:
            # If not, convert
            self.timestamp_string = str(self.timestamp_string)

        # Convert to MySQL format: Remove the 'T' and the microseconds
        vsa_fmtd_timestamp_str = (self.timestamp_string.replace('T', ' ')).split('.')[0]

        # Convert back to a datetime object
        vsa_fmtd_timestamp = datetime.strptime(vsa_fmtd_timestamp_str, "%Y-%m-%d %H:%M:%S")

        # Convert the UTC timestamp to local time
        # This apparently works because 'America/Denver' is specified in settings.py?
        vsa_fmtd_timestamp_local = vsa_fmtd_timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)

        # Convert back to a string
        vsa_fmtd_timestamp_local_str = str(vsa_fmtd_timestamp_local)

        # Remove the offset data from the string
        vsa_fmtd_timestamp_local_str_final = vsa_fmtd_timestamp_local_str[0:19]

        # Return the final result
        return vsa_fmtd_timestamp_local_str_final




    # For LOB APP DB to MySQL
    def lobapp_to_mysql(self):
        # LOB app / postgres format: 2022-08-06 12:47:07.79843
        # LOB app times are UTC

        # Needfuls
        from django.utils import timezone as djtimezone
        from datetime import datetime, timezone
        import time
        import pytz

        # Make sure a string was supplied
        if isinstance(self.timestamp_string, str) == False:
            # If not, convert
            self.timestamp_string = str(self.timestamp_string)

        # Handle the empty timestamp_string
        if not self.timestamp_string or '1000-01-01 00:00:00' in self.timestamp_string:
            lobapp_fmtd_timestamp_local_str_final = '1000-01-01 00:00:00'
            return lobapp_fmtd_timestamp_local_str_final

        # Convert to MySQL format: Remove the microseconds
        lobapp_fmtd_timestamp_str = self.timestamp_string.split('.')[0]

        # Convert back to a datetime object
        lobapp_fmtd_timestamp = datetime.strptime(lobapp_fmtd_timestamp_str, "%Y-%m-%d %H:%M:%S")

        # Convert the UTC timestamp to local time
        # This apparently works because 'America/Denver' is specified in settings.py?
        lobapp_fmtd_timestamp_local = lobapp_fmtd_timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)

        # Convert back to a string
        lobapp_fmtd_timestamp_local_str = str(lobapp_fmtd_timestamp_local)

        # Remove the offset data from the string
        lobapp_fmtd_timestamp_local_str_final = lobapp_fmtd_timestamp_local_str[0:19]

        # Return the final result
        return lobapp_fmtd_timestamp_local_str_final



##########################


