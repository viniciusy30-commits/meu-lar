import bpy, math, os, sys
from mathutils import Vector

# Usage: blender -b --python tools/render_city2.py -- <glb> <output_dir>
args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
glb = args[0] if args else "app/src/main/assets/hds/city2.glb"
out = args[1] if len(args)>1 else "city2-renders"
os.makedirs(out, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=glb)

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not meshes:
    raise RuntimeError("GLB não contém malhas")
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (mn+mx)*0.5
size = mx-mn
print("CITY2_BOUNDS", tuple(mn), tuple(mx), "SIZE", tuple(size), "MESHES", len(meshes))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 48
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'AgX - Medium High Contrast'
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
cam_data.lens = 50

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def render(name, target, location, scale, res=(1400,900)):
    cam.location = location
    aim(cam, target)
    cam_data.ortho_scale = scale
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(out, name+".png")
    bpy.ops.render.render(write_still=True)

span = max(size.x, size.z)
# Orthographic overview from above and a low angled overview
render("01_top_overview", (center.x, center.y, center.z),
       (center.x, center.y+span*1.25+size.y, center.z+0.001), span*1.08)
render("02_oblique_overview", center,
       (center.x+span*0.85, center.y+span*0.75, center.z+span*0.95), span*1.18)

# Four quadrant views, useful for checking roads, lots and repeated house geometry.
for idx, (sx,sz) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)], start=1):
    target = Vector((center.x+sx*size.x*0.23, center.y, center.z+sz*size.z*0.23))
    loc = Vector((target.x+span*0.25, target.y+span*0.48, target.z+span*0.30))
    render("0%d_quadrant"% (idx+2), target, loc, span*0.55)

# Camera-height street inspection at the center and four cardinal points.
for idx, (dx,dz) in enumerate([(0,0),(0.22,0),(-0.22,0),(0,0.22),(0,-0.22)], start=1):
    tx = center.x + size.x*dx
    tz = center.z + size.z*dz
    target = Vector((tx, mn.y+size.y*0.20, tz))
    loc = Vector((tx+span*0.12, mn.y+max(2.0,size.y*0.16), tz+span*0.22))
    render("street_%02d"%idx, target, loc, span*0.28, (1280,800))

with open(os.path.join(out,"render_report.txt"),"w") as f:
    f.write("GLB: "+glb+"\n")
    f.write("Meshes: "+str(len(meshes))+"\n")
    f.write("Bounds min: "+str(tuple(mn))+"\n")
    f.write("Bounds max: "+str(tuple(mx))+"\n")
    f.write("Size: "+str(tuple(size))+"\n")
print("RENDER_COMPLETE", out)
