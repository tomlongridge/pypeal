CREATE TABLE @db_name.`reports` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `description` VARCHAR(128) NULL,
    `ringer_id` INT UNSIGNED NULL,
    `tower_id` INT UNSIGNED NULL,
    `ring_id` INT UNSIGNED NULL,
    `date_from` DATE NULL,
    `date_to` DATE NULL,
    `created_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_reports_ringer` FOREIGN KEY (`ringer_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_reports_tower` FOREIGN KEY (`tower_id`) REFERENCES `towers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_reports_ring` FOREIGN KEY (`ring_id`) REFERENCES `rings` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
