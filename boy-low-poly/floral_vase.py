import bpy, math, random
from mathutils import Vector
from math import sin,cos,pi
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
out=Path('D:/Godot/Models/Kitchen')
rng=random.Random(12)
def mat(name,color,metal=0,rough=.42):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    for key,val in [('Base Color',(*color,1)),('Metallic',metal),('Roughness',rough)]: p.inputs[key].default_value=val
    return m
jade=mat('Celadon glaze',(.095,.31,.265),.12,.19)
gold=mat('Champagne rim',(.68,.41,.16),.8,.24)
green=mat('Olive stems',(.09,.19,.059))
leaf=mat('Sage foliage',(.14,.30,.18))
colors=[mat('Apricot silk',(.92,.39,.24)),mat('Warm ivory',(.98,.84,.65)),mat('Blush pink',(.94,.54,.48))]
root=bpy.data.objects.new('FloralTableVase',None)
bpy.context.collection.objects.link(root)
def surface(name,rows,m,wrap=False):
    w=len(rows[0])
    f=[(j*w+i,j*w+(i+1)%w,(j+1)*w+(i+1)%w,(j+1)*w+i) for j in range(len(rows)-1) for i in range(w if wrap else w-1)]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(sum(rows,[]),[],f)
    mesh.materials.append(m)
    o=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.parent=root
    for p in mesh.polygons:p.use_smooth=True
    return o
def vessel(name,profile,m):
    rows=[]
    for z,r,flute in profile:
        rows.append([((r+flute*cos(20*a))*cos(a),(r+flute*cos(20*a))*sin(a),z) for a in [2*pi*i/160 for i in range(160)]])
    surface(name,rows,m,True)
vessel('Fluted ceramic',[(0,.0001,0),(0,.033,0),(.006,.036,0),(.018,.041,.001),(.045,.054,.002),(.073,.057,.002),(.096,.05,.0018),(.115,.036,.001),(.125,.027,0),(.137,.028,0),(.139,.025,0),(.126,.024,0),(.10,.034,0),(.04,.024,0),(.012,.0001,0)],jade)
for z,r in [(.006,.036),(.137,.028)]:
    vessel('Gilt bead',[(z-.001,r,0),(z,r+.0012,0),(z+.001,r,0)],gold)
def stem(end):
    x,y,z=end
    return [Vector((x*t*t,y*t*t,.078+(z-.078)*t)) for t in [i/12 for i in range(13)]]
for k in range(7):
    a=k*2.40
    radius=.0 if k==0 else .042+.009*(k%2)
    c=Vector((radius*cos(a),radius*sin(a),.255 if k==0 else .197+.011*(k%4)))
    path=stem(c)
    surface('Flower stem',[[p+Vector((.0017*cos(i*pi/4),.0017*sin(i*pi/4),0)) for i in range(8)] for p in path],green,True)
    for j in (6,8):
        d=Vector((cos(a+j),sin(a+j),.50))
        cross=Vector((-d.y,d.x,0))
        rows=[]
        for i in range(11):
            t=i/10
            mid=path[j]+d*.047*t+Vector((0,0,.009*sin(pi*t)))
            w=.010*sin(pi*t)+.0001
            rows.append([mid-cross*w,mid+Vector((0,0,.0025*sin(pi*t))),mid+cross*w])
        surface('Lanceolate leaf',rows,leaf)
    tilt=.46 if k else .1
    axis=Vector((sin(tilt)*cos(a),sin(tilt)*sin(a),cos(tilt)))
    u=Vector((-sin(a),cos(a),0))
    v=axis.cross(u)
    for layer,(count,r,h) in enumerate([(10,.028,.015),(8,.021,.021),(6,.014,.024),(4,.007,.026)]):
        for j in range(count):
            angle=2*pi*j/count+layer*.89+rng.uniform(-.06,.06)
            rows=[]
            for n in range(9):
                t=n/8
                row=[]
                for b in range(11):
                    s=b/5-1
                    ang=angle+s*(.12+.55*t)
                    rad=r*(.10+.90*t**1.45)*(1-.19*s*s)
                    z=h*(1-(1-t)**2)-.003*s*s*t+.001*cos(3*pi*s)*t**4
                    row.append(c+(u*cos(ang)+v*sin(ang))*rad+axis*z)
                rows.append(row)
            surface('Garden rose petal',rows,colors[k%3])
# Batch each material into a mesh for a lightweight table prop.
for material in [jade,gold,green,leaf,*colors]:
    bpy.ops.object.select_all(action='DESELECT')
    parts=[o for o in root.children if o.data.materials[0]==material]
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=str(out/'FloralTableVase.glb'))
scene=bpy.context.scene
scene.world=bpy.data.worlds.new('Studio')
scene.world.color=(.32,.32,.32)
bpy.ops.mesh.primitive_plane_add(size=200)
bpy.context.object.data.materials.append(mat('Backdrop',(.18,.16,.14)))
def aim(o):o.rotation_euler=(Vector((0,0,.143))-o.location).to_track_quat('-Z','Y').to_euler()
for pos,power,size in [((-.4,-.45,.65),12,.48),((.45,-.25,.4),7,.4),((.1,.38,.56),11,.35)]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    o=bpy.context.object
    o.data.energy=power
    o.data.size=size
    aim(o)
bpy.ops.object.camera_add(location=(.40,-.65,.41))
scene.camera=bpy.context.object
aim(scene.camera)
scene.camera.data.type='ORTHO'
scene.camera.data.ortho_scale=.345
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=640
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.filepath=str(out/'FloralTableVase.png')
bpy.ops.render.render(write_still=True)
