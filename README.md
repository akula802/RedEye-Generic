# RedEye (Generic)

This is a generic, sanitized version of a Django app I wrote for an old employer. It was a temporary tool that we needed to gain some insights on computer issues at remote locations. It was never deployed to the public Internet, just hosted on an Ubuntu VM locally (using Nginx and gunicorn).

I called it RedEye because it was almost entirely created between the hours of 9:00 PM and 2:00 AM, fueled by junk food and irish whiskey. It started primarily as a learning project for me, and after several months of work, it became a thing we could actually use.

Due to the sanitization etc. this app will not do anything useful if you clone it. I just wanted to put it here as an example of my past work.

All of the necessary secrets must be stored in a ".env" file at the app root, which is ignored by git and not checked into version control. This repo contains an example of how the file is structured.

# Description:

This is a "proof of concept" web app that collects and combines data about remote PCs.

Summary: Python+Django, running on an Ubuntu server, with Nginx and gunicorn. The main app database is MySQL.

The app pulls gate PC information from the Kaseya API and an internal LOB app database.

The Kaseya objects and the LOB app objects are tied together using a Custom Field in Kaseya. The Custom Field called 'LAC-DeviceName' and contains a string value lifted from a config file on the Kaseya agent (in a separate script, previously run). It acts as a sort of foreign key to match the LOB data with the Kaseya agent data.

The data is collected every 30 minutes, and there is currently a 91-day retention set via MySQL scheduled task.

The most recent collection set is served out as a new REST API at http://192.168.0.20/api/gate_servers

To use the app, people had to register for a user account and get an auth token for the REST API.

# API Returned Objects

app_run_number = Integer (bigint) representing the run counter of the data collector. Each time the app goes out to collect data, this number increments by 1. Will be used to calculate uptime metrics.

app_rmm_fetch_time = Timestamp of when the app connected to the Kaseya API.

app_lob_fetch_time = Timestamp of when the app connected to the LOB app database.

rmm_agent_id = The unique ID assigned to the gate PC agent in Kaseya. Used mainly for the custom field lookups.

lob_computer_name = The name of the computer object in the LOB app database.

rmm_lac_computer_name = A custom field in Kaseya, populated by a separate script (previously run). Contains a string lifted from a config file on the local machine, matching the 'lob_computer_name' value. This custom field ties the Kaseya computer object to the computer object in the LOB app database.

rmm_computer_name = The hostname of the computer, as reported by Kaseya.

rmm_agent_name = The Kaseya agent name is often different from the hostname. Helpful to track down computers that are not named following any standard format (e.g. there is a PC with a default / auto-generated hostname of DESKTOP-T1TSKQLH which is not helpful. But the agent name is Facility-1030.LOB.root which is more descriptive).

lob_location = The PC's facility ID in the LOB app database (e.g. Facility 1030).

rmm_lob_file_type = Another custom field in Kaseya, populated by a separate script (previously run). Contains a string value representing the name of a hardware vendor, for the machine the PC controls.

rmm_last_reboot = Timestamp of the last reboot, retrieved from Kaseya.

rmm_last_checkin = Timestamp of the last agent checkin to Kaseya. Useful for partial up/down status (e.g. rmm_last_checkin more than 10 minutes ago means the agent could be offline), and for tracking how long an agent goes offline for.

lob_last_lob_update = Timestamp of the last time the LOB app service on the PC updated info from the LOB app on the Internet.

lob_last_lob_query = Timestamp of the last time the LOB app service on the PC checked the LOB app for available updates.

rmm_ram_mbytes = The amount of RAM the computer has, expressed in Mb, as reported by Kaseya.

rmm_cpu_type = The CPU type reported by Kaseya (e.g. if we see values like ‘Atom’ or ‘Pentium’ it’s a sign the PC is super old).

rmm_agent_is_offline = A boolean (true|false) of whether the agent is actively checking in to Kaseya. An on offline=true value means the agent is not checking in, and could be offline. This is a condition that must be alerted on an investigated.

lob_agent_is_offline = A boolean (true|false) of whether the agent is querying the LOB app for code updates. An offline=true value means the LOB app service has not checked into the LOB app for 10+ minutes. Based on the timestamp in the ‘lob_last_lob_query’ value.

rmm_uptime_score = A float representing the percentage of time the agent has been online and functional in Kaseya, covering the retention period of the database records (right now, it’s the past 91 days). A score of 100.00 means there were no problems. The math works like: [((# of app runs where rmm_agent_offline = False) / (# of total app runs for this agent)) x 100]

lob_uptime_score = A float representing the percentage of time the agent has been online and functional in the LOB app, covering the retention period of the database records (right now, it’s the past 91 days). A score of 100.00 means there were no problems. The math works like: [((# of app runs where lob_agent_offline = False) / (# of total app runs for this agent)) x 100]

