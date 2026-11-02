import json
S=[
# (fbx, nome, cat, preco, rug)
("sofa01","Sofá de canto",0,260,0),("sofa02","Sofá baixo",0,220,0),("casual-chair01","Poltrona",0,110,0),
("coffee-table01","Mesa de centro redonda",0,80,0),("coffee-table02","Mesa de centro baixa",0,70,0),
("cabinet01","Aparador",0,160,0),("shelf01","Estante aberta",0,120,0),("stool01","Pufe azul",0,35,0),
("stool02","Banqueta",0,40,0),("small-cushion01","Almofada grande",0,15,0),("small-cushion02","Almofada comprida",0,15,0),
("speaker01","Caixa de som",0,45,0),
("office-desk01","Escrivaninha",1,130,0),("office-chair01","Cadeira de escritório",1,140,0),
("computer-case","Gabinete de PC",1,90,0),("monitor01","Monitor curvo",1,180,0),("keyboard01","Teclado",1,30,0),
("computer-mouse","Mouse",1,15,0),("mouse_pad01","Mousepad grande",1,15,1),("desk-lamp01","Luminária articulada",1,40,0),
("desk-lamp02","Luminária de mesa",1,30,0),("clock01","Relógio de mesa",1,20,0),
("basket01","Cesto de vime",2,25,0),("bin","Lixeira",2,20,0),("storage-box01","Caixa organizadora",2,18,0),
("tray01","Bandeja de madeira",2,15,0),("tissue-box","Caixa de lenços",2,8,0),
("carpet01","Tapete longo 1",3,60,1),("carpet02","Tapete longo 2",3,60,1),("carpet03","Tapete redondo 1",3,45,1),
("carpet04","Tapete redondo 2",3,45,1),("indoor-plant01","Planta grande",3,70,0),("pot-cactus","Cacto",3,15,0),
("vase01","Vaso de vime",3,18,0),("vase02","Vaso de argila",3,18,0),("vase03","Vaso com folhas",3,30,0),
("vase04","Vaso baixo",3,12,0),("vase05","Vaso fino",3,14,0),("book01","Livro",3,8,0),("book02","Livro pequeno",3,8,0),
("books01","Pilha de livros",3,14,0),("books02","Livros deitados",3,14,0),("books03","Livros em pé",3,16,0),
("sculpture01","Escultura",3,55,0),("trinket-abs","Letreiro ABS",3,25,0),("trinket-duck","Patinho amarelo",3,12,0),
("trinket_wooden_ball","Bola de madeira",3,10,0),("photo-frame01","Porta-retrato largo",3,12,0),("photo-frame02","Porta-retrato alto",3,12,0)]
json.dump({f:dict(nome=n,cat=c,preco=p,rug=r) for f,n,c,p,r in S},open('mobspec.json','w'),ensure_ascii=False,indent=1)
print(len(S))
