# Core library and/or django imports
from django.db import models

# 3rd-party imports

# Local app imports

#############################


# Model for the temporary authorization items for Kaseya VSA
class VsaAuthTokens(models.Model):
    vsa_auth_token_timestamp = models.DateTimeField(default='1992-04-21 00:04:20')
    vsa_auth_token = models.TextField()


# Model for the combined data table
# Table name in the database is 'infoget_gateservers'
class LobServers(models.Model)
    app_run_number = models.BigIntegerField(blank=True, null=True)
    app_rmm_fetch_time = models.DateTimeField(blank=True, null=True)
    app_lob_fetch_time = models.DateTimeField(blank=True, null=True)
    rmm_agent_id = models.BigIntegerField(blank=True, null=True)
    lob_computer_name = models.CharField(max_length=100, blank=True, null=True)  # This must match rmm_lac_computer_name
    rmm_lac_computer_name = models.CharField(max_length=200, blank=True, null=True)  # This is a Custom Field in Kaseya
    rmm_computer_name = models.CharField(max_length=100, blank=True, null=True)
    rmm_agent_name = models.CharField(max_length=100, blank=True, null=True)
    lob_location = models.CharField(max_length=25, blank=True, null=True)  
    rmm_lac_file_type = models.CharField(max_length=100, blank=True, null=True)
    rmm_last_reboot = models.DateTimeField(blank=True, null=True)
    rmm_last_checkin = models.DateTimeField(blank=True, null=True)
    lob_last_lob_update = models.DateTimeField(blank=True, null=True)
    lob_last_lob_query = models.DateTimeField(blank=True, null=True)
    rmm_ram_mbytes = models.IntegerField(blank=True, null=True)
    rmm_cpu_type = models.CharField(max_length=100, blank=True, null=True)
    rmm_agent_is_offline = models.BooleanField(blank=True, null=True)
    lob_agent_is_offline = models.BooleanField(blank=True, null=True)
    rmm_uptime_score = models.FloatField(blank=True, null=True)
    lob_uptime_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.app_rmm_fetch_time
        return self.app_lob_fetch_time
        return self.rmm_agent_id
        return self.lob_computer_name
        return self.rmm_lac_computer_name
        return self.rmm_computer_name
        return self.rmm_agent_name
        return self.lob_location
        return self.rmm_lac_file_type
        return self.rmm_last_reboot
        return self.rmm_last_checkin
        return self.lob_last_lob_update
        return self.lob_last_lob_query
        return self.rmm_ram_mbytes
        return self.rmm_cpu_type
        return self.rmm_agent_is_offline
        return self.lob_agent_is_offline
        return self.rmm_uptime_score
        return self.lob_uptime_score



