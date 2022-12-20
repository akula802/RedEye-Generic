CREATE EVENT `ApplyRetention-infoget_gateservers`
	ON SCHEDULE EVERY 6 HOUR STARTS '2022-10-27 22:00:00'
	ON COMPLETION PRESERVE
	ENABLE
	COMMENT 'Deletes rows from {redshift.infoget_gateservers} older than 91 days'

DO
	
	/* Deletes rows older than 30 days from redshift.infoget_gateservers */
	DELETE FROM redshift.infoget_gateservers igs
	WHERE igs.app_rmm_fetch_time < DATE_SUB(NOW(), INTERVAL 91 DAY)
