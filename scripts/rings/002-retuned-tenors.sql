-- Stoke St Milborough, Shropshire
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (15014, NULL, NULL);
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (15014, 'Original 8', '2020/07/08');

SET @old_ring_id = LAST_INSERT_ID();

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @old_ring_id, id, role, NULL
FROM bells
WHERE tower_id = 15014;

UPDATE @db_name.`ringbells` SET bell_weight = 1870 WHERE ring_id = @old_ring_id AND bell_role = 8;


-- Presteigne, Powys
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (14991, NULL, NULL);
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (14991, 'Original 8', '2016/05/01');

SET @old_ring_id = LAST_INSERT_ID();

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @old_ring_id, id, role, NULL
FROM bells
WHERE tower_id = 14991;

UPDATE @db_name.`ringbells` SET bell_weight = 1690 WHERE ring_id = @old_ring_id AND bell_role = 8;