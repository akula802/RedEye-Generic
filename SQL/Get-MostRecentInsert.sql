USE redeye;

SELECT * FROM infoget_lobservers ils

WHERE ils.app_rmm_fetch_time > DATE_SUB(NOW(), INTERVAL 10 MINUTE)
ORDER BY ils.red_computer_name
