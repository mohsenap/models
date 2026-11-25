import bpy
from pathlib import Path
from math import pi
from mathutils import Vector

out = Path(bpy.data.filepath).parent
scene = bpy.context.scene

def duplicate(source, parent=None):
    copy = source.copy()
    scene.collection.objects.link(copy)
    copy.parent = parent
    for part in source.children:
        duplicate(part, copy)
    return copy

rows = {
    2: [(x, y) for y in (-43,-34) for x in (8,16,24,32,40)],
    4: [(x,-23) for x in (9,20,31,42)],
    8: [(x,-12) for x in (10,25,40)],
    12: [(x,0) for x in (10,25,40)],
    24: [(x,12) for x in (10,25,40)],
}
chair = bpy.data.objects['Round4_Chair_01']
total_tables = total_chairs = 0
for kind,side in [('Rectangular',-1),('Round',1)]:
    for seats,positions in rows.items():
        if seats == 2:
            bpy.ops.import_scene.gltf(filepath=str(out/f'Saloon{kind}TableForTwo.glb'))
            table, = [o for o in bpy.context.selected_objects if not o.parent]
            pattern = [(chair,Vector((0,s*(.77 if side==1 else .70),0)),0 if s==1 else pi) for s in (-1,1)]
        else:
            table = bpy.data.objects[f'{kind}Dining_{seats}']
            pattern = []
            for i in range(1,seats+1):
                seat = bpy.data.objects[f'{kind}{seats}_Chair_{i:02}']
                pattern.append((seat,seat.location-table.location,seat.rotation_euler.z))
        for index,(x,y) in enumerate(positions,1):
            desk = table if index==1 else duplicate(table)
            desk.name = f'{kind}Dining_{seats}_{index:02}'
            desk.location = (side*x,y,0)
            total_tables += 1
            for i,(original,offset,angle) in enumerate(pattern,1):
                seat = original if seats!=2 and index==1 else duplicate(original)
                seat.name = f'{desk.name}_Chair_{i:02}'
                seat.location = desk.location + offset
                seat.rotation_euler.z = angle
                total_chairs += 1
assert (total_tables,total_chairs)==(46,336)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'))
