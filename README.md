# RedEye (Generic)

This is a generic, sanitized version of a Django app I wrote for an old employer. It was a temporary tool that we needed to gain some insights on computer issues at remote locations. It was never deployed to the public Internet, just hosted on an Ubuntu VM locally (using Nginx and gunicorn).

I called it RedEye because it was almost entirely created between the hours of 9:00 PM and 2:00 AM, fueled by junk food and irish whiskey. It started primarily as a learning project for me, and after several months of work, it became a thing we could actually use.

Due to the sanitization etc. this app will not do anything useful if you clone it. I just wanted to put it here as an example of my past work.

All of the necessary secrets must be stored in a ".env" file at the app root, which is ignored by git and not checked into version control. This repo contains an example of how the file is structured.

# Description:

This is a "proof of concept" web app that collects and combines data about remote PCs.

Summary: Python+Django, running on an Ubuntu server, with Nginx and gunicorn. The main app database is MySQL.

The app pulls gate PC information from the Kaseya API and an internal LOB app database.

The Kaseya objects and the LOB app objects are tied together using a Custom Field in Kaseya. The Custom Field called 'custom_field_1' and contains a string value lifted from a config file on the Kaseya agent. It acts as a sort of foreign key to match the LOB data with the Kaseya agent data.

The data is collected every 30 minutes, and there is currently a 91-day retention set via MySQL scheduled task.

The most recent collection set is served out as a new REST API at http://192.168.0.20/api/gate_servers

To use the app, people had to register for a user account and get an auth token for the REST API.
