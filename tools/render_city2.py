import bpy, math, os, sys, json, struct
from mathutils import Vector, Matrix

# Renderiza a Cidade 2 exatamente como Hds.kt: GLB fornece as malhas-base;
# city2.json fornece as 2.837 instâncias, transformações e deslocamento do lote.
args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
glb = args[0] if args else "app/src/main/assets/hds/city2.glb"
js_path = args[1] if len(args)>1 else "app/src/main/assets/hds/city2.json"
out = args[2] if len(args)>2 else "city2-renders"
os.makedirs(out, exist_ok=True)

with open(glb, "rb") as f:
    raw = f.read()
if raw[:4] != b"glTF":
    raise RuntimeError("Arquivo não é GLB 2.0")
json_len = struct.unpack_from("<I", raw, 12)[0]
gltf = json.loads(raw[20:20+json_len].decode("utf-8"))
with open(js_path, "r", encoding="utf-8") as f:
    city = json.load(f)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=glb)
source_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not source_objects:
    raise RuntimeError("GLB não contém malhas")

# O importador preserva o nome do nó glTF no objeto Blender.
by_name = {}
for o in source_objects:
    by_name.setdefault(o.name, o)
node_names = [n.get("name", "n%d" % i) for i,n in enumerate(gltf.get("nodes", []))]
missing = []
for i, n in enumerate(gltf.get("nodes", [])):
    if "mesh" not in n:
        continue
    name = node_names[i]
    if name not in by_name and name + ".001" not in by_name:
        missing.append((i, name))

res = city["res"]
# Hds.kt: lotX0=-10, lotX1=W+10, lotZ0=-22, lotZ1=H+9.
# W/H vêm dos limites do mapa; o centro do lote em Z é (H-13)/2.
world_w = float(city["bounds"][2] - city["bounds"][0])
world_h = float(city["bounds"][3] - city["bounds"][1])
ox = world_w * 0.5 - float(res[0])
oz = (world_h - 13.0) * 0.5 - float(res[1])

collection = bpy.context.scene.collection
created = 0
unmapped = {}
# matriz row-major igual à usada em Hds.addPrim()
for row in city.get("inst", []):
    node_i = int(row[0])
    if node_i < 0 or node_i >= len(node_names):
        unmapped[node_i] = unmapped.get(node_i, 0) + 1
        continue
    name = node_names[node_i]
    src = by_name.get(name)
    if src is None:
        # Blender acrescenta sufixos quando há nomes repetidos.
        src = next((o for o in source_objects if o.name == name or o.name.startswith(name + ".")), None)
    if src is None:
        unmapped[node_i] = unmapped.get(node_i, 0) + 1
        continue
    m = [float(v) for v in row[1:13]]
    mat = Matrix(((m[0],m[1],m[2],m[3]+ox),
                  (m[4],m[5],m[6],m[7]),
                  (m[8],m[9],m[10],m[11]+oz),
                  (0,0,0,1)))
    ob = src.copy()
    ob.data = src.data
    ob.name = "CITY2_INST_%04d_NODE_%d" % (created, node_i)
    collection.objects.link(ob)
    ob.parent = None
    ob.matrix_world = mat
    created += 1

# Remove as malhas-base fora de suas posições reais; mantém somente as instâncias.
for o in source_objects:
    bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
if not pts:
    raise RuntimeError("Nenhuma instância foi reconstruída; nós sem correspondência: %s" % missing[:20])
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (mn+mx)*0.5
size = mx-mn
print("CITY2_INSTANCE_RENDER", "instances", created, "meshes", len(meshes), "missing", len(unmapped), "bounds", tuple(mn), tuple(mx))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 48
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
world = bpy.data.worlds.new("City2World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.24,0.27,0.31,1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sun_data = bpy.data.lights.new("City2Sun", 'SUN')
sun_data.energy = 2.0
sun = bpy.data.objects.new("City2Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(28), math.radians(-22), math.radians(-28))
cam_data = bpy.data.cameras.new("City2Camera")
cam = bpy.data.objects.new("City2Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = 'ORTHO'
cam_data.clip_start = 0.1
cam_data.clip_end = 10000

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def render(name, target, location, scale, reso=(1400,900)):
    cam.location = location
    aim(cam, target)
    cam_data.ortho_scale = scale
    scene.render.resolution_x, scene.render.resolution_y = reso
    scene.render.filepath = os.path.join(out, name+".png")
    bpy.ops.render.render(write_still=True)

# No jogo, Y é vertical e X/Z são os eixos do chão.
span = max(size.x, size.z)
render("01_top_overview", center, (center.x, mx.y + span*1.15, center.z), span*1.08)
render("02_oblique_overview", center, (center.x+span*0.82, center.y+span*0.92, center.z-span*0.82), span*1.18)
for idx, (sx,sz) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)], start=1):
    target = Vector((center.x+sx*size.x*0.23, center.y, center.z+sz*size.z*0.23))
    loc = Vector((target.x+span*0.25, mx.y+span*0.38, target.z-span*0.48))
    render("0%d_quadrant"% (idx+2), target, loc, span*0.55)
for idx, (dx,dz) in enumerate([(0,0),(0.22,0),(-0.22,0),(0,0.22),(0,-0.22)], start=1):
    tx = center.x + size.x*dx
    tz = center.z + size.z*dz
    target = Vector((tx, center.y, tz))
    loc = Vector((tx+span*0.12, center.y+span*0.42, tz-span*0.22))
    render("street_%02d"%idx, target, loc, span*0.28, (1280,800))

with open(os.path.join(out,"render_report.txt"),"w") as f:
    f.write("GLB: "+glb+"\nJSON: "+js_path+"\n")
    f.write("Instâncias reconstruídas: "+str(created)+"\n")
    f.write("Malhas renderizadas: "+str(len(meshes))+"\n")
    f.write("Nós sem correspondência: "+str(len(unmapped))+" "+str(unmapped)+"\n")
    f.write("Bounds min: "+str(tuple(mn))+"\nBounds max: "+str(tuple(mx))+"\nSize: "+str(tuple(size))+"\n")
    f.write("Node names sample: "+str(node_names[:30])+"\n")
print("RENDER_COMPLETE", out)
