from shared.db import execute
execute('DELETE FROM sales')
execute('DELETE FROM insurance')
execute('UPDATE vehicles SET sold=0')
execute("DELETE FROM prospects WHERE email LIKE '%@test.pe'")
print('Reset done')
