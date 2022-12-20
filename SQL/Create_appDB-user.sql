# Create the app user in MySQL
#USE redeye;
#CREATE USER 'redeye-app'@'localhost' IDENTIFIED BY '#SuperSecurePassword#'

# Grant the rights - this is probably more than actually necessary for the user
USE redeye;
GRANT ALL PRIVILEGES ON `redeye` . * TO 'redeye-app'@'localhost';
FLUSH PRIVILEGES;
