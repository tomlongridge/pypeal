CREATE TABLE @db_name.`associations` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(128) NOT NULL,
    `is_user_added` TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`)
);

ALTER TABLE @db_name.`associations` AUTO_INCREMENT=10000;
