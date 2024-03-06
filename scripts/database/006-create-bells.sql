CREATE TABLE @db_name.`bells` (
    `id` int NOT NULL AUTO_INCREMENT,
    `tower_id` INT NOT NULL,
    `role` tinyint UNSIGNED NOT NULL,
    `weight` INT NULL,
    `note` VARCHAR(10) NULL,
    `cast_year` INT NULL,
    `founder` VARCHAR(128) NULL,
    PRIMARY KEY (`id` ),
    CONSTRAINT `fk_bell_tower` FOREIGN KEY (`tower_id`) REFERENCES `towers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
