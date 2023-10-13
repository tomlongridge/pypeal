CREATE TABLE @db_name.`pealmethods` (
    `peal_id` int UNSIGNED NOT NULL,
    `method_id` VARCHAR(10) NOT NULL,
    `changes` int UNSIGNED,
    PRIMARY KEY (`peal_id`, `method_id`),
    UNIQUE KEY `id_unique` (`peal_id`, `method_id`),
    CONSTRAINT `fk_pealmethods_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_pealmethods_method` FOREIGN KEY (`method_id`) REFERENCES `methods` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);