CREATE TABLE @db_name.`ringerpeals` (
  `ringer_id` int NOT NULL,
  `peal_count` int DEFAULT '0',
  PRIMARY KEY (`ringer_id`),
  UNIQUE KEY `id_unique` (`ringer_id`),
  CONSTRAINT `fk_ringerpeals_ringer` FOREIGN KEY (`ringer_id`) REFERENCES `ringerpeals` (`ringer_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
)