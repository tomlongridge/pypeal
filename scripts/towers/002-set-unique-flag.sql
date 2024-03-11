SET SQL_SAFE_UPDATES=0;
UPDATE towers as t
SET is_unique_place = 1
WHERE NOT EXISTS (
	SELECT 1 FROM (
		SELECT id
		FROM towers as ut
		WHERE ut.id <> t.id
		AND ut.place = t.place
		AND ut.sub_place = t.sub_place
        AND ut.county = t.county
        AND ut.country = t.country
	) tbl_temp
);
SET SQL_SAFE_UPDATES=1;