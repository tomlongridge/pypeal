SET @tower_id = -13019;
SET @ring_id = -1000001;

-- 1987 augmentation

INSERT INTO  @db_name.`rings` (id, tower_id, description, date_removed) VALUES (@ring_id, @tower_id, 'Re-tuned 8', '1987/01/16');

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @ring_id, id, role - 2, NULL
FROM bells
WHERE tower_id = @tower_id AND role > 2;

UPDATE @db_name.`ringbells` SET bell_weight = 662 WHERE ring_id = @ring_id AND bell_role = 1;
UPDATE @db_name.`ringbells` SET bell_weight = 730 WHERE ring_id = @ring_id AND bell_role = 2;
UPDATE @db_name.`ringbells` SET bell_weight = 743 WHERE ring_id = @ring_id AND bell_role = 3;
UPDATE @db_name.`ringbells` SET bell_weight = 898 WHERE ring_id = @ring_id AND bell_role = 4;
UPDATE @db_name.`ringbells` SET bell_weight = 1043 WHERE ring_id = @ring_id AND bell_role = 5;
UPDATE @db_name.`ringbells` SET bell_weight = 1304 WHERE ring_id = @ring_id AND bell_role = 6;
UPDATE @db_name.`ringbells` SET bell_weight = 1603 WHERE ring_id = @ring_id AND bell_role = 7;
UPDATE @db_name.`ringbells` SET bell_weight = 2196 WHERE ring_id = @ring_id AND bell_role = 8;

-- 1948 re-hang

SET @ring_id = -1000004;

INSERT INTO  @db_name.`rings` (id, tower_id, description, date_removed) VALUES (@ring_id, @tower_id, 'Original 8', '1948/03/20');

INSERT INTO  @db_name.`ringbells` (ring_id, bell_id, bell_role, bell_weight)
SELECT @ring_id, id, role - 2, NULL
FROM bells
WHERE tower_id = @tower_id AND role > 2;

UPDATE @db_name.`ringbells` SET bell_weight = 672 WHERE ring_id = @ring_id AND bell_role = 1;
UPDATE @db_name.`ringbells` SET bell_weight = 784 WHERE ring_id = @ring_id AND bell_role = 2;
UPDATE @db_name.`ringbells` SET bell_weight = 784 WHERE ring_id = @ring_id AND bell_role = 3;
UPDATE @db_name.`ringbells` SET bell_weight = 952 WHERE ring_id = @ring_id AND bell_role = 4;
UPDATE @db_name.`ringbells` SET bell_weight = 1120 WHERE ring_id = @ring_id AND bell_role = 5;
UPDATE @db_name.`ringbells` SET bell_weight = 1370 WHERE ring_id = @ring_id AND bell_role = 6;
UPDATE @db_name.`ringbells` SET bell_weight = 1680 WHERE ring_id = @ring_id AND bell_role = 7;
UPDATE @db_name.`ringbells` SET bell_weight = 2352 WHERE ring_id = @ring_id AND bell_role = 8;