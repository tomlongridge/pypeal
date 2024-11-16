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

-- St Juliot, St Juliot, Cornwall, England, GB
SET @tower_id = -15966;

INSERT INTO @db_name.`bells` (`id`, `tower_id`, `role`, `weight`, `note`)
VALUES (-37531, @tower_id, 1, 332, 'F'),
       (-37532, @tower_id, 2, 463, 'E♭'),
       (-37533, @tower_id, 3, 466, 'D♭'),
       (-37534, @tower_id, 4, 502, 'C'),
       (-37535, @tower_id, 5, 541, 'B♭'),
       (-5773,  @tower_id, 6, 908, 'A♭');

-- Ropley, S Peter, Hampshire, England, GB
SET @tower_id = -13242;

INSERT INTO @db_name.`bells` (`id`, `tower_id`, `role`, `weight`, `note`)
VALUES (-36777, @tower_id, 1, 510, 'D♯'),
       (-36778, @tower_id, 2, 591, 'C♯'),
       (-36779, @tower_id, 3, 786, 'B'),
       (-36780, @tower_id, 4, 849, 'A♯'),
       (-36781, @tower_id, 5, 1223, 'G♯'),
       (-5632,  @tower_id, 6, 1703, 'F♯');