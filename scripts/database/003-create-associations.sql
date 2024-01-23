CREATE TABLE @db_name.`associations` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(128) NOT NULL,
    `is_user_added` TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`)
);
