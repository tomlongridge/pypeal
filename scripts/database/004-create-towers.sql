CREATE TABLE @db_name.`towers` (
    `id` INT NOT NULL,
    `place` VARCHAR(128) NOT NULL,
    `sub_place` VARCHAR(128) NULL,
    `dedication` VARCHAR(128) NOT NULL,
    `county` VARCHAR(128) NOT NULL,
    `country` VARCHAR(128) NOT NULL,
    `country_code` VARCHAR(2) NOT NULL,
    `latitude` FLOAT NULL,
    `longitude` FLOAT NULL,
    `bells` INT NOT NULL,
    `tenor_weight` INT NOT NULL,
    `tenor_note` VARCHAR(10) NOT NULL,
    PRIMARY KEY (`id`)
);
