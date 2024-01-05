CREATE TABLE @db_name.`peals` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `bellboard_id` INT UNSIGNED NULL,
    `type` TINYINT UNSIGNED NOT NULL,
    `bell_type` TINYINT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `ring_id` INT UNSIGNED NULL,
    `place` VARCHAR(128) NULL,
    `sub_place` VARCHAR(128) NULL,
    `association_id` INT UNSIGNED NULL,
    `address` VARCHAR(128) NULL,
    `dedication` VARCHAR(128) NULL,
    `county` VARCHAR(128) NULL,
    `country` VARCHAR(128) NULL,
    `changes` INT UNSIGNED NULL,
    `stage` TINYINT UNSIGNED NULL,
    `classification` VARCHAR(45) NULL,
    `is_variable_cover` BOOL DEFAULT FALSE NOT NULL,
    `num_methods` TINYINT UNSIGNED DEFAULT NULL,
    `num_principles` TINYINT UNSIGNED DEFAULT NULL,
    `num_variants` TINYINT UNSIGNED DEFAULT NULL,
    `method_id` VARCHAR(10) NULL,
    `title` VARCHAR(128) NOT NULL,
    `published_title` VARCHAR(128) NULL,
    `detail` VARCHAR(1024) NULL,
    `composer_id` INT UNSIGNED NULL,
    `composition_note` VARCHAR(128) NULL,
    `composition_url` VARCHAR(128) NULL,
    `duration` INT UNSIGNED NULL,
    `tenor_weight` INT UNSIGNED NULL,
    `tenor_note` VARCHAR(10) NULL,
    `event_url` VARCHAR(128) NULL,
    `muffles` TINYINT UNSIGNED NULL,
    `external_reference` VARCHAR(128) NULL,
    `bellboard_submitter` VARCHAR(128) NULL,
    `bellboard_submitted_date` DATE NULL,
    `created_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
    UNIQUE INDEX `bellboard_id_UNIQUE` (`bellboard_id` ASC) VISIBLE,
    CONSTRAINT `fk_peals_ring` FOREIGN KEY (`ring_id`) REFERENCES `rings` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_peals_method` FOREIGN KEY (`method_id`) REFERENCES `methods` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_peals_association` FOREIGN KEY (`association_id`) REFERENCES `associations` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_peals_composer` FOREIGN KEY (`composer_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
