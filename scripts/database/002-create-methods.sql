CREATE TABLE @db_name.`methods` (
    `id` VARCHAR(10) NOT NULL,
    `stage` TINYINT UNSIGNED NOT NULL,
    `is_differential` BOOL DEFAULT FALSE NOT NULL,
    `is_little` BOOL DEFAULT FALSE NOT NULL,
    `is_plain` BOOL DEFAULT FALSE NOT NULL,
    `is_treble_dodging` BOOL DEFAULT FALSE NOT NULL,
    `classification` VARCHAR(128) NULL,
    `name` VARCHAR(512) NULL,
    `searchable_name` VARCHAR(512) NULL,
    `full_name` VARCHAR(512) NOT NULL,
    PRIMARY KEY (`id`)
);
