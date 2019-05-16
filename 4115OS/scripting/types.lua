table1 = {}
table1[1], table1[2], table1[3] = 10, 10, 20

summator = function(some_table)
	sum = 0
	for counter = 1, #some_table, 1 do
		sum = sum + some_table[counter]
	end
	return sum
end

table2 = {10, 20, 30, 40, 50}

print("The sum is: ", summator(table1))
print("The sum is: ", summator(table2))