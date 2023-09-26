CREATE TABLE @db_name.`peals` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `bellboard_id` INT UNSIGNED NULL,
    `date` DATE NOT NULL,
    `place` VARCHAR(45) NOT NULL,
    `association` VARCHAR(128) NULL,
    `address_dedication` VARCHAR(128) NULL,
    `county` VARCHAR(45) NULL,
    `changes` INT UNSIGNED NULL,
    `title` VARCHAR(45) NULL,
    `duration` INT UNSIGNED NULL,
    `tenor_weight` VARCHAR(45) NULL,
    `tenor_tone` VARCHAR(45) NULL,
    PRIMARY KEY (`id`)
);
