CREATE TABLE @db_name.`pealringers` (
    `peal_id` int UNSIGNED NOT NULL,
    `ringer_id` int UNSIGNED NOT NULL,
    `bell_num` tinyint UNSIGNED  DEFAULT 0,
    `bell_id` int UNSIGNED NULL,
    `is_conductor` tinyint(1) NOT NULL DEFAULT 0,
    `note` VARCHAR(255) NULL,
    `bell_weight` INT NULL,
    `bell_note` VARCHAR(10) NULL,
    `bell_cast_year` INT NULL,
    `bell_founder` VARCHAR(128) NULL,
    PRIMARY KEY (`peal_id`, `ringer_id`, `bell_num`),
    UNIQUE KEY `id_unique` (`peal_id`, `ringer_id`, `bell_num`),
    CONSTRAINT `fk_pealringers_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_pealringers_ringer` FOREIGN KEY (`ringer_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_pealringers_bells` FOREIGN KEY (`bell_id`) REFERENCES `bells` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);