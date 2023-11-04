CREATE TABLE @db_name.`towers` (
    `id` INT UNSIGNED NOT NULL,
    `towerbase_id` INT UNSIGNED NULL,
    `place` VARCHAR(128) NOT NULL,
    `sub_place` VARCHAR(128) NULL,
    `dedication` VARCHAR(128) NOT NULL,
    `county` VARCHAR(128) NOT NULL,
    `country` VARCHAR(128) NOT NULL,
    `country_code` VARCHAR(2) NOT NULL,
    `latitude` FLOAT NULL,
    `longitude` FLOAT NULL,
    `bells` INT NOT NULL,
    `tenor_weight` INT UNSIGNED NOT NULL,
    `tenor_note` VARCHAR(10) NOT NULL,
    PRIMARY KEY (`id`)
);
