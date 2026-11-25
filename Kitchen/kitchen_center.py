import bpy
import bmesh
from pathlib import Path
from math import pi

scene = bpy.context.scene
out = Path(bpy.data.filepath).parent
collection = bpy.data.collections.new('11 Centre islands and service pass')
scene.collection.children.link(collection)
source = bpy.data.objects['Kitchen_North_01']
parts = [source, *source.children_recursive]
walnut = bpy.data.materials['Walnut']
stone = bpy.data.materials['Quartzite']
metal = bpy.data.materials['Satin stainless steel']
brass = bpy.data.materials['Brushed champagne door trim']
proxy = bpy.data.materials['Invisible collision geometry']
cache = {}

def block(name, parent, pos, size, mat, bevel=.005):
    key = (size,mat.name,bevel)
    if key not in cache:
        bm = bmesh.new()
        for v in bmesh.ops.create_cube(bm,size=1)['verts']:
            for i in range(3):
                v.co[i] *= size[i]
        if bevel:
            bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES')
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)
        if mat in (walnut,stone):
            uv=mesh.uv_layers.new().data
            for face in mesh.polygons:
                axis=max(range(3),key=lambda i:abs(face.normal[i]))
                a,b=[(1,2),(0,2),(0,1)][axis]
                for i in face.loop_indices:
                    v=mesh.vertices[mesh.loops[i].vertex_index].co
                    uv[i].uv=(.5+v[a]/1.9,.5+v[b]/1.9)
        cache[key]=mesh
    o=bpy.data.objects.new(parent.name+'_'+name,cache[key])
    collection.objects.link(o)
    o.parent=parent
    o.location=pos
    if mat==proxy:
        o.display_type='WIRE'
    return o

for i,x in enumerate((-25,-15,-5,5,15,25),1):
    mapping={}
    for original in parts:
        copy=original.copy()
        copy.name=original.name.replace(source.name,f'CentreIsland{i:02}')
        collection.objects.link(copy)
        mapping[original]=copy
    for original,copy in mapping.items():
        copy.parent=mapping.get(original.parent)
    root=mapping[source]
    root.location=(x,36,0)
    root.rotation_euler.z=pi/2 if x<0 else -pi/2
    # The rear steel frame supports the upper cabinets independently of a wall.
    for j,u in enumerate((-3.90,-2.15,-.35,1.45,3.90)):
        size=(.052,.052,2.30)
        block(f'Upright{j}',root,(u,.724,1.15),size,metal)
        block(f'Upright{j}-colonly',root,(u,.724,1.15),size,proxy,0)
    for z in (1.625,2.27):
        block('SupportRail',root,(0,.699,z),(7.9,.05,.05),metal)

for i,x in enumerate((-7.5,-3.9,3.9,7.5),1):
    p=bpy.data.objects.new(f'ServicePass{i:02}',None)
    collection.objects.link(p)
    p.location=(x,24.45,0)
    p.empty_display_size=.12
    def piece(name,pos,size,mat,bevel=.005):
        block(name,p,pos,size,mat,bevel)
        block(name+'-colonly',p,pos,size,proxy,0)
    piece('HonedStoneTop',(0,0,.902),(3.20,.90,.036),stone,.008)
    piece('Underframe',(0,0,.86),(3.10,.80,.046),metal)
    piece('WalnutFascia',(0,-.398,.784),(3.10,.032,.115),walnut)
    block('BrassInlay',p,(0,-.416,.819),(3.04,.003,.006),brass,.001)
    piece('LowerLandingShelf',(0,0,.28),(3.06,.74,.032),metal)
    for j,(dx,dy) in enumerate(((-1.50,-.35),(-1.50,.35),(1.50,-.35),(1.50,.35))):
        piece(f'Leg{j}',(dx,dy,.424),(.05,.05,.848),metal)

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'))
