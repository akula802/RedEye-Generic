USE redeye;
#SELECT COUNT(*) FROM infoget_gateservers igs
SELECT * FROM infoget_gateservers igs
#DELETE FROM infoget_gateservers igs

WHERE igs.app_rmm_fetch_time > DATE_SUB(NOW(), INTERVAL 10 MINUTE)
ORDER BY igs.red_computer_name
