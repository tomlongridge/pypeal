#!/bin/bash

echo "Ready to clear database?"
read -p "Press enter to continue"

mysql --user root pypeal_test < 000.sql

for i in {1..22}
do
    file="$(seq -f "%03g" $i $i).sql"

    echo "Run up to test $file"
    read -p "Press enter to continue"

    echo "source 000.sql" > $file
    echo "" >> $file
    echo "" >> $file
    mysqldump pypeal_test associations ringers peals pealmethods pealringers pealfootnotes pealphotos --user root --no-create-db --no-create-info >> $file
done