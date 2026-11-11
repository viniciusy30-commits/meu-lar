import csv,io,json,re
t=open('localization.txt',encoding='utf-8').read()
rows=csv.reader(io.StringIO(t))
hdr=next(rows); pi=hdr.index('Portuguese'); ei=hdr.index('English')
L={}
for r in rows:
    if len(r)>pi and r[0]: L[r[0]]=(r[pi].strip() or r[ei].strip(), r[ei].strip())
json.dump(L,open('loc.json','w'),ensure_ascii=False)
print(len(L))
for k,v in L.items():
    if re.search(r'cat|categ|shop-|furniture',k) and len(k)<60: print(k,'=',v[0])