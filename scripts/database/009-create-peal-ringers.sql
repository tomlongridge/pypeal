CREATE TABLE @db_name.`pealringers` (
    `peal_id` int UNSIGNED NOT NULL,
    `ringer_id` int UNSIGNED NOT NULL,
    `bell_num` tinyint UNSIGNED,
    `bell` tinyint UNSIGNED,
    `is_conductor` tinyint(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`peal_id`, `ringer_id`, `bell`),
    UNIQUE KEY `id_unique` (`peal_id`, `ringer_id`, `bell`),
    CONSTRAINT `fk_pealringers_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_pealringers_ringer` FOREIGN KEY (`ringer_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);