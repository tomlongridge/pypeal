CREATE TABLE @db_name.`ringers` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `last_name` VARCHAR(45) NOT NULL,
    `given_names` VARCHAR(45) NULL,
    `title` VARCHAR(45) NULL,
    `is_composer` BOOLEAN NULL DEFAULT FALSE,
    `link_id` INT UNSIGNED NULL,
    `date_to` DATE NULL,
    `home_tower_id` INT NULL,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
    CONSTRAINT `fk_ringers_link` FOREIGN KEY (`link_id`) REFERENCES `ringers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_ringers_tower` FOREIGN KEY (`home_tower_id`) REFERENCES `towers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);