CREATE TABLE @db_name.`ringbells` (
    `bell_id` int UNSIGNED NOT NULL,
    `ring_id` INT UNSIGNED NOT NULL,
    `bell_role` tinyint UNSIGNED NOT NULL,
    PRIMARY KEY (`bell_id` ),
    CONSTRAINT `fk_ringbells_bell` FOREIGN KEY (`bell_id`) REFERENCES `bells` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT `fk_ringbells_ring` FOREIGN KEY (`ring_id`) REFERENCES `rings` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
);
