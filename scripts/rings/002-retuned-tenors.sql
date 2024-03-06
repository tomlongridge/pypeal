-- Stoke St Milborough, Shropshire
SET @tower_id = -15015;
SET @ring_id = -1000002;

INSERT INTO  @db_name.`rings` (id, tower_id, description, date_removed) VALUES (@ring_id, @tower_id, 'Original 8', '2020/07/08');

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @ring_id, id, role, NULL
FROM bells
WHERE tower_id = @tower_id;

UPDATE @db_name.`ringbells` SET bell_weight = 1870 WHERE ring_id = @ring_id AND bell_role = 8;


-- Presteigne, Powys
SET @tower_id = -14991;
SET @ring_id = -1000003;

INSERT INTO  @db_name.`rings` (id, tower_id, description, date_removed) VALUES (@ring_id, @tower_id, 'Original 8', '2016/05/01');

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @ring_id, id, role, NULL
FROM bells
WHERE tower_id = @tower_id;

UPDATE @db_name.`ringbells` SET bell_weight = 1690 WHERE ring_id = @ring_id AND bell_role = 8;