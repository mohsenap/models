import bpy, re, math, sys
from pathlib import Path
from mathutils import Vector
k=Path('D:/Godot/Models/Kitchen')
def mat(name,color,metal=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal
    return m
def box(name,loc,dims,m,bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object
    o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(m)
    b=o.modifiers.new('Rounded moulding','BEVEL')
    b.width=bevel
    b.segments=4
    o.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return o
def export(name):
    bpy.ops.export_scene.gltf(filepath=str(k/(name+'.glb')),export_apply=True,export_lights=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
brass=mat('Antique brass',(.46,.245,.075),.78)
wood=mat('Oiled walnut',(.135,.055,.024))
dark=mat('Dark walnut bead',(.062,.024,.011))
for inset,width,depth,m in [(0,.14,.09,wood),(.018,.024,.12,dark),(.052,.012,.116,brass),(.119,.028,.13,brass)]:
    w,h=3.2-2*inset,4.8-2*inset
    for s in [-1,1]:
        box('Frame rail',(0,-depth/2,2.4+s*(h-width)/2),(w,depth,width),m)
        box('Frame stile',(s*(w-width)/2,-depth/2,2.4),(width,depth,h-2*width),m)
m=mat('Painted canvas',(1,1,1))
tex=m.node_tree.nodes.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(sys.argv[-1])
m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,-.08,2.4),rotation=(math.pi/2,0,0))
o=bpy.context.object
o.name='Cyrus overlooking Pasargadae'
o.scale=(1.47,2.27,1)
o.data.materials.append(m)
export('CyrusFramedPortrait')
for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o,do_unlink=True)
box('Wall rose',(0,-.035,0),(.32,.07,.18),brass,.03)
for x in [-.11,.11]:box('Cantilever arm',(x,-.22,0),(.032,.42,.032),brass)
box('Brushed brass picture light',(0,-.44,-.02),(1.24,.13,.13),brass,.055)
lens=mat('Halogen lens',(1,.86,.64))
p=lens.node_tree.nodes.get('Principled BSDF')
p.inputs['Emission Color'].default_value=(1,.78,.48,1)
p.inputs['Emission Strength'].default_value=4
box('Warm glass aperture',(0,-.44,-.082),(1.12,.076,.016),lens)
for x in [-.33,.33]:
    bpy.ops.object.light_add(type='SPOT',location=(x,-.44,-.09))
    o=bpy.context.object
    o.rotation_euler=Vector((0,.34,-1)).to_track_quat('-Z','Y').to_euler()
    o.data.energy=55
    o.data.color=(1,.79,.55)
    o.data.spot_size=math.radians(86)
    o.data.spot_blend=.75
export('GalleryHalogen')
bpy.ops.wm.open_mainfile(filepath=str(k/'Restaurant.blend'))
tables=[o for o in bpy.context.scene.objects if re.fullmatch(r'RectangularDining_\d+(?:_\d+)?',o.name)]
assert len(tables)==23
bpy.ops.import_scene.gltf(filepath=str(k/'Celadon-Daisies.glb'))
src=next(o for o in bpy.context.selected_objects if o.type=='MESH')
for t in tables:
    pts=[t.matrix_world.inverted() @ o.matrix_world @ Vector(v) for o in [t,*t.children_recursive] if o.type=='MESH' and 'chair' not in o.name.lower() and all('chair' not in p.name.lower() for p in [o.parent] if p) for v in o.bound_box]
    low,high=[Vector([f(p[i] for p in pts) for i in range(3)]) for f in [min,max]]
    axis=0 if high.x-low.x>=high.y-low.y else 1
    for j,f in enumerate((.25,.75) if int(t.name.split('_')[1])>=8 else (.5,)):
        pos=(low+high)/2
        pos.z=high.z
        pos[axis]=low[axis]+f*(high[axis]-low[axis])
        vase=src.copy()
        bpy.context.scene.collection.objects.link(vase)
        vase.parent=t
        vase.location=pos
        vase.name=t.name+'_Celadon_'+str(j+1)
bpy.data.objects.remove(src,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(k/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(k/'Restaurant.glb'))
