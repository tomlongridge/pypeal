-- Cleator Moor, St John the Evangelist, Cumbria, England, GB
-- Bells now removed
SET @tower_id = -1000001;

INSERT INTO  @db_name.`towers` (`id`, `place`, `dedication`, `county`, `country`, `country_code`, `latitude`, `longitude`, `bells`,
                                `tenor_weight`, `tenor_note`)
VALUES (@tower_id, 'Cleator Moor', 'St John the Evangelist', 'Cumbria', 'England', 'GB', 54.523602, -3.5260077, 8, 2430, 'E');

-- St Juliot, St Juliot, Cornwall, England, GB
-- Unringable
SET @tower_id = -15966;

INSERT INTO  @db_name.`towers` (`id`, `place`, `dedication`, `county`, `country`, `country_code`, `latitude`, `longitude`, `bells`,
                                `tenor_weight`, `tenor_note`)
VALUES (@tower_id, 'St Juliot', 'St Juliot', 'Cornwall', 'England', 'GB', 50.69048, -4.65039, 6, 908, 'A♭');