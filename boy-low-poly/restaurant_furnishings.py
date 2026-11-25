import bpy
from pathlib import Path
from math import sin, cos, pi, ceil, atan2
from mathutils import Vector
out=Path(bpy.data.filepath).parent
scene=bpy.context.scene
lib=(out/'dining_furniture.py').read_text(encoding='utf-8-sig')
exec(lib[lib.index('def finish'):lib.index('bronze=')])
exec(lib[lib.index('def asset'):lib.index('chair=asset')])
walnut,stone,brass=[bpy.data.materials[n] for n in ('Walnut','Quartzite','Brushed champagne door trim')]
steel=bpy.data.materials['Satin stainless steel']
rubber=finish('Graphite rubber',(.028,.033,.034),.85)
velvet=finish('Deep peacock velvet',(.018,.105,.098),.76)
velvet.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.58
light=finish('Opal fluorescent diffuser',(.89,.92,.90),.32)
shader=light.node_tree.nodes.get('Principled BSDF')
shader.inputs['Emission Color'].default_value=(1,.96,.87,1)
shader.inputs['Emission Strength'].default_value=3
def box(name,w,d,r,z,h,mat,x=0,y=0):
    o=slab(name,outline(w,d,r),[(z,.985),(z+.002,1),(z+h-.002,1),(z+h,.985)],mat)
    o.location.x=x
    o.location.y=y
    return o
def finish_asset():
    bpy.ops.object.select_all(action='DESELECT')
    parts=list(root.children)
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    export()
    return root
def copy_at(master,name,pos,angle=0,parent=None):
    o=master.copy()
    scene.collection.objects.link(o)
    o.name=name
    o.parent=parent
    o.location=pos
    o.rotation_euler.z=angle
    for original in master.children:
        child=original.copy()
        scene.collection.objects.link(child)
        child.parent=o
    return o
masters=[]
asset('LargeRecyclingBin')
box('Pedal bin shell',.65,.6,.09,.06,.85,steel)
box('Raised lid',.68,.63,.095,.91,.065,rubber)
box('Lid insert',.64,.59,.09,.969,.018,steel)
box('Step pedal',.27,.15,.035,.05,.035,rubber,0,-.31)
box('Non-slip base',.64,.59,.085,.005,.06,rubber)
bin_master=finish_asset()
masters.append(bin_master)
groups=[o for o in scene.objects if o.name.startswith('CabinetPanelGroup') and o.parent is None]
assert len(groups)==10
for i,g in enumerate(groups,1):
    copy_at(bin_master,f'RecyclingBin_{i:02}',(4.34,0,0),parent=g)
group=bpy.data.objects['CabinetPanelGroup']
saved=group.location.copy()
group.location=(0,0,0)
root=group
export()
group.location=saved

asset('TwoTierFoodServiceCart')
for z in (.23,.84):
    box('Tray surround',1.02,.58,.055,z,.035,brass)
    box('Tray surface',.993,.552,.045,z+.026,.022,walnut)
    for y in (-.276,.276):
        box('Raised tray edge',.98,.02,.009,z+.036,.034,brass,0,y)
for x in (-.47,.47):
    for y in (-.25,.25):
        shaft('Frame upright',(x,y,.13),(x,y,.965),.015,.015,steel)
        shaft('Swivel wheel',(x-.025,y,.074),(x+.025,y,.074),.073,.073,rubber)
        shaft('Axle cap',(x-.029,y,.074),(x+.029,y,.074),.024,.024,brass)
    box('Push handle',.038,.53,.018,.945,.038,walnut,x)
cart=finish_asset()
masters.append(cart)
for i,(x,y) in enumerate([(-33,31),(-31,31),(-29,31),(29,31),(31,31),(33,31)],1):
    copy_at(cart,f'ServiceCart_{i:02}',(x,y,0))

asset('FlushCeilingFluorescent')
box('Champagne bezel',1.4,.60,.045,-.065,.065,brass)
box('Recessed gasket',1.36,.56,.035,-.072,.012,rubber)
box('Opal lens',1.33,.53,.03,-.082,.017,light)
lamp=finish_asset()
masters.append(lamp)
slab_obj=bpy.data.objects['Full ceiling slab']
ceiling=min((slab_obj.matrix_world@Vector(c)).z for c in slab_obj.bound_box)
vents=[o.matrix_world.translation.copy() for o in scene.objects if o.name.startswith('ExtractionHood')]
for ix in range(-16,17):
    for iy in range(-16,17):
        x,y=3*ix,3*iy
        if any(abs(x-v.x)<1.04 and abs(y-v.y)<.64 for v in vents): continue
        copy_at(lamp,f'CeilingLamp_{ix+17:02}_{iy+17:02}',(x,y,ceiling))

asset('SaloonDiningChair')
seat=outline(.60,.55,.12)
slab('Walnut seat rail',seat,[(.38,.91),(.392,.96),(.422,.99)],walnut)
slab('Velvet cushion',seat,[(.419,.98),(.44,1),(.476,.98),(.495,.84)],velvet)
for sx in (-1,1):
    for sy in (-1,1):
        foot=Vector((sx*.26,sy*.23,.005))
        hip=Vector((sx*.217,sy*.196,.401))
        join=foot.lerp(hip,.15)
        shaft('Brass sabot',foot,join,.014,.017,brass)
        shaft('Walnut leg',join,hip,.017,.028,walnut)
# Upholstered horseshoe shell rises from the arm tips to a fluted back.
rings=[]
for i in range(97):
    a=-.45+(pi+.90)*i/96
    height=.685+.245*max(sin(a),0)
    radius=1+.026*cos(24*a)
    rings.append([((.277+dr)*cos(a),(.247+dr)*sin(a),z) for dr,z in
        [(.027,.405),(.036,height-.028),(.028,height),(.002,height+.004),(-.020*radius,height-.022),(-.022*radius,.435)]])
loft('Channelled wraparound velvet shell',rings,velvet)
loft('Champagne back trim',[[((.309+d)*cos(a),(.279+d)*sin(a),.46+z) for d,z in [(0,0),(.004,0),(.004,.009),(0,.009)]] for a in [-.45+(pi+.90)*i/96 for i in range(97)]],brass)
chair=finish_asset()
masters.append(chair)

for circular in (False,True):
    for col,count in enumerate((4,8,12,24)):
        kind='Round' if circular else 'Rectangular'
        asset(f'Saloon{kind}TableFor{count}')
        radius=max(.65,.78*count/(2*pi))
        length=max(1.35,(count//2-1)*.82)
        shape=[(radius*cos(i*pi/64),radius*sin(i*pi/64)) for i in range(128)] if circular else outline(length,1.18,.10)
        slab('Quartzite dining surface',shape,[(.736,.996),(.742,1),(.764,1),(.77,.995)],stone,1.4)
        slab('Walnut apron',shape,[(.692,.945),(.736,.987)],walnut)
        slab('Champagne edge',shape,[(.73,.987),(.738,.995)],brass)
        if circular:
            supports=[(0,0)] if count<=4 else [(radius*.54*cos(2*pi*i/4),radius*.54*sin(2*pi*i/4)) for i in range(4)]
        else:
            k=max(1,ceil(length/2.2))
            supports=[(length*((i+.5)/k-.5),0) for i in range(k)]
        for x,y in supports:
            shaft('Weighted foot',(x,y,0),(x,y,.045),.32,.27,brass)
            shaft('Turned walnut pedestal',(x,y,.04),(x,y,.69),.145,.112,walnut)
            shaft('Mounting collar',(x,y,.68),(x,y,.739),.16,.22,brass)
        table=finish_asset()
        masters.append(table)
        cx=(-35,-15,14,34)[col]
        cy=-30 if circular else -7
        copy_at(table,f'{kind}Dining_{count}',(cx,cy,0))
        if circular:
            chairs=[((radius+.32)*cos(a),(radius+.32)*sin(a)) for a in [2*pi*i/count for i in range(count)]]
        else:
            n=count//2-1
            chairs=[(length*((i+.5)/n-.5),s*.90) for s in (-1,1) for i in range(n)]+[(s*(length/2+.32),0) for s in (-1,1)]
        for i,(x,y) in enumerate(chairs,1):
            angle=atan2(-x,y) if circular or abs(y)<.01 else (0 if y>0 else pi)
            copy_at(chair,f'{kind}{count}_Chair_{i:02}',(cx+x,cy+y,0),angle)
for master in masters:
    for o in [*master.children,master]: bpy.data.objects.remove(o,do_unlink=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'))
