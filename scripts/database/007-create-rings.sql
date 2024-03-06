CREATE TABLE @db_name.`rings` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `tower_id` INT NOT NULL,
    `description` VARCHAR(128) NULL,
    `date_removed` DATE NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_ring_tower` FOREIGN KEY (`tower_id`) REFERENCES `towers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
