CREATE TABLE @db_name.`towers` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `towerbase_id` INT UNSIGNED NULL,
    `place` VARCHAR(128) NOT NULL,
    `sub_place` VARCHAR(128) NULL,
    `dedication` VARCHAR(128) NULL,
    `county` VARCHAR(128) NOT NULL,
    `country` VARCHAR(128) NOT NULL,
    `country_code` VARCHAR(2) NOT NULL,
    `latitude` FLOAT NULL,
    `longitude` FLOAT NULL,
    `bells` INT NOT NULL,
    `tenor_weight` INT UNSIGNED NOT NULL,
    `tenor_note` VARCHAR(10) NULL,
    `is_unique_place` TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`)
);
