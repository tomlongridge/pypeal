CREATE TABLE @db_name.`pealphotos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `peal_id` INT UNSIGNED NOT NULL,
    `caption` VARCHAR(512) NULL,
    `credit` VARCHAR(128) NULL,
    `url` VARCHAR(128) NOT NULL,
    `photo` LONGBLOB NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_pealphotos_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
