CREATE TABLE @db_name.`pealringers` (
  `ringer_id` int UNSIGNED NOT NULL,
  `peal_id` int UNSIGNED NOT NULL,
  `bell` int UNSIGNED,
  `is_conductor` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ringer_id`, `peal_id`, `bell`),
  UNIQUE KEY `id_unique` (`ringer_id`, `peal_id`, `bell`),
  CONSTRAINT `fk_pealringers_ringer` FOREIGN KEY (`ringer_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_pealringers_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
)