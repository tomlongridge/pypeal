INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (13019, NULL, NULL);
INSERT INTO  @db_name.`rings` (tower_id, description, date_removed) VALUES (13019, 'Original 8', '1987/01/16');

SET @old_ring_id = LAST_INSERT_ID();

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @old_ring_id, id, role - 2, NULL
FROM bells
WHERE tower_id = 13019 AND role > 2;

UPDATE @db_name.`ringbells` SET bell_weight = 662 WHERE ring_id = @old_ring_id AND bell_role = 1;
UPDATE @db_name.`ringbells` SET bell_weight = 730 WHERE ring_id = @old_ring_id AND bell_role = 2;
UPDATE @db_name.`ringbells` SET bell_weight = 743 WHERE ring_id = @old_ring_id AND bell_role = 3;
UPDATE @db_name.`ringbells` SET bell_weight = 898 WHERE ring_id = @old_ring_id AND bell_role = 4;
UPDATE @db_name.`ringbells` SET bell_weight = 1040 WHERE ring_id = @old_ring_id AND bell_role = 5;
UPDATE @db_name.`ringbells` SET bell_weight = 1300 WHERE ring_id = @old_ring_id AND bell_role = 6;
UPDATE @db_name.`ringbells` SET bell_weight = 1600 WHERE ring_id = @old_ring_id AND bell_role = 7;
UPDATE @db_name.`ringbells` SET bell_weight = 2200 WHERE ring_id = @old_ring_id AND bell_role = 8;