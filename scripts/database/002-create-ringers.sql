CREATE TABLE @db_name.`ringers` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `last_name` VARCHAR(45) NOT NULL,
    `given_names` VARCHAR(45) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE
);