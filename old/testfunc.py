def sqlDict(c):
	ret = list()
	for f in c.fetchall():
		c = 0
		vals = dict()
		for i in f.keys():
			vals[i] = f[c]
			c+=1
		ret.append(vals)
	return ret

def sqlDataString(data):
	ret = ''
	first = True
	for i in data:
		if first:
			first = False
		else:
			ret+=','
		ret += "`"+str(i)+"`="+"'"+str(data[i])+"'"
	return ret
