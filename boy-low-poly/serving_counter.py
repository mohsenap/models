import bpy
import bmesh
from pathlib import Path

out = Path(bpy.data.filepath).parent
scene = bpy.context.scene
collection = bpy.data.collections['11 Centre islands and service pass']
for name in ['ServicePass01','ServicePass02','ServicePass03','ServicePass04','MDFServingCounter']:
    old = bpy.data.objects.get(name)
    if old:
        for child in list(old.children_recursive):
            bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(old,do_unlink=True)

root=bpy.data.objects.new('MDFServingCounter',None)
collection.objects.link(root)
walnut=bpy.data.materials['Walnut']
brass=bpy.data.materials['Brushed champagne door trim']
proxy=bpy.data.materials['Invisible collision geometry']
top=bpy.data.materials.new('Warm mushroom satin laminate on MDF')
top.diffuse_color=(.32,.265,.21,1)
top.use_nodes=True
shader=top.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value=top.diffuse_color
shader.inputs['Roughness'].default_value=.42
cache={}

def part(name,pos,size,material,radius=.004):
    key=(size,material,radius)
    if key not in cache:
        bm=bmesh.new()
        for v in bmesh.ops.create_cube(bm,size=1)['verts']:
            for i in range(3):
                v.co[i]*=size[i]
        if radius:
            bmesh.ops.bevel(bm,geom=list(bm.edges),offset=radius,segments=4,affect='EDGES')
        mesh=bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(material)
        if material==walnut:
            uv=mesh.uv_layers.new().data
            for face in mesh.polygons:
                axis=max(range(3),key=lambda i:abs(face.normal[i]))
                a,b=[(1,2),(0,2),(0,1)][axis]
                for i in face.loop_indices:
                    v=mesh.vertices[mesh.loops[i].vertex_index].co
                    uv[i].uv=(.5+v[a]/1.30,.5+v[b]/1.30)
        cache[key]=mesh
    o=bpy.data.objects.new(name,cache[key])
    collection.objects.link(o)
    o.parent=root
    o.location=pos
    if material==proxy:
        o.display_type='WIRE'

def board(name,pos,size,material,radius=.004):
    part(name,pos,size,material,radius)
    part(name+'-colonly',pos,size,proxy,0)

board('Continuous laminate worktop',(0,0,1.176),(16,.90,.048),top,.009)
board('Full walnut MDF front',(0,-.417,.576),(15.96,.04,1.152),walnut)
part('Champagne edge detail',(0,-.439,1.138),(15.96,.004,.008),brass,.001)
for i in range(9):
    x=(i-4)*1.99
    board(f'MDF support {i+1:02}',(x,.012,.576),(.036,.818,1.152),walnut)
for i in range(8):
    x=(i-3.5)*1.99
    board(f'Chef shelf {i+1:02}',(x,.015,.48),(1.954,.76,.03),walnut)
for side in (-1,1):
    for i in range(28):
        x=side*(7.94-i*.042)
        part(f'Reeded end {side} {i:02}',(x,-.44,.565),(.022,.012,1.116),walnut,.005)

bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'MDFServingCounter.glb'),use_selection=True)
root.location=(0,24.45,0)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'))
