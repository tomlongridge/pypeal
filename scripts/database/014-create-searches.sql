CREATE TABLE @db_name.`pealsearches` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `description` VARCHAR(128) NULL,
    `ringer_name` VARCHAR(128) NULL,
    `date_from` DATE NULL,
    `date_to` DATE NULL,
    `tower_id` INT UNSIGNED NULL,
    `place` VARCHAR(128) NULL,
    `region` VARCHAR(128) NULL,
    `address` VARCHAR(128) NULL,
    `association` VARCHAR(128) NULL,
    `title` VARCHAR(128) NULL,
    `bell_type` TINYINT(2) UNSIGNED NULL,
    `order_by_submission_date` TINYINT(1) DEFAULT 0 NOT NULL,
    `order_descending` TINYINT(1) DEFAULT 0 NOT NULL,
    `poll_frequency` INT UNSIGNED NULL,
    `created_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_run_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
);
