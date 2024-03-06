-- Cleator Moor, St John the Evangelist, Cumbria, England, GB
SET @tower_id = -1000001;

INSERT INTO @db_name.`bells` (`id`, `tower_id`, `role`)
VALUES (-1000001, @tower_id, 1),
       (-1000002, @tower_id, 2),
       (-1000003, @tower_id, 3),
       (-1000004, @tower_id, 4),
       (-1000005, @tower_id, 5),
       (-1000006, @tower_id, 6),
       (-1000007, @tower_id, 7);

INSERT INTO @db_name.`bells` (`id`, `tower_id`, `role`, `weight`, `note`)
VALUES (-1000008, @tower_id, 8, 2430, 'E');