# Core imports

# 3rd-party imports
from rest_framework import serializers

# Local app imports
from .models import LobServers


###########################


class Api_LobServers_serializer (serializers.ModelSerializer):
    class Meta:
        model = LobServers
        fields = ['app_run_number', 'app_rmm_fetch_time', 'app_lob_fetch_time', 'rmm_agent_id', 'lob_computer_name', 'rmm_lac_computer_name', 'rmm_computer_name', 'rmm_agent_name', 'lob_location', 'rmm_lac_file_type', 'rmm_last_reboot', 'rmm_last_checkin', 'lob_last_lob_update', 'lob_last_lob_query', 'rmm_ram_mbytes', 'rmm_cpu_type', 'rmm_agent_is_offline', 'lob_agent_is_offline', 'rmm_uptime_score', 'lob_uptime_score']
        #fields = '__all__'

