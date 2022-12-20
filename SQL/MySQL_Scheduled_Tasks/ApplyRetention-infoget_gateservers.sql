CREATE EVENT `ApplyRetention-infoget_lobservers`
	ON SCHEDULE EVERY 6 HOUR STARTS '2022-10-27 22:00:00'
	ON COMPLETION PRESERVE
	ENABLE
	COMMENT 'Deletes rows from {redeye.infoget_lobservers} older than 91 days'

DO
	
	/* Deletes rows older than 30 days from redeye.infoget_lobservers */
	DELETE FROM redeye.infoget_lobservers igs
	WHERE igs.app_rmm_fetch_time < DATE_SUB(NOW(), INTERVAL 91 DAY)
