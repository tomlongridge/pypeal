CREATE TABLE @db_name.`pealfootnotes` (
    `peal_id` INT UNSIGNED NOT NULL,
    `footnote_num` INT NOT NULL,
    `bell` int UNSIGNED NULL,
    `text` VARCHAR(512) NOT NULL,
    PRIMARY KEY (`peal_id`, `footnote_num`),
    CONSTRAINT `fk_pealfootnotes_peal` FOREIGN KEY (`peal_id`) REFERENCES `peals` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
