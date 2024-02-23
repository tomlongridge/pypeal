INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (15014, NULL, NULL);
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (15014, 'Original 8', '2020/07/08');

SET @old_ring_id = LAST_INSERT_ID();

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @old_ring_id, id, role, NULL
FROM bells
WHERE tower_id = 15014;

UPDATE @db_name.`ringbells` SET bell_weight = 662 WHERE ring_id = @old_ring_id AND bell_role = 1; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 730 WHERE ring_id = @old_ring_id AND bell_role = 2; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 743 WHERE ring_id = @old_ring_id AND bell_role = 3; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 898 WHERE ring_id = @old_ring_id AND bell_role = 4; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 1040 WHERE ring_id = @old_ring_id AND bell_role = 5; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 1300 WHERE ring_id = @old_ring_id AND bell_role = 6; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 1600 WHERE ring_id = @old_ring_id AND bell_role = 7; -- Unsure of weight
UPDATE @db_name.`ringbells` SET bell_weight = 1870 WHERE ring_id = @old_ring_id AND bell_role = 8;