import bpy
import numpy as np
from pathlib import Path
from mathutils import Vector

out = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, rgb, metal=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, alpha)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    for key, value in [('Base Color', (*rgb, 1)), ('Metallic', metal), ('Alpha', alpha), ('Roughness', .24 if alpha < 1 else .45)]:
        p.inputs[key].default_value = value
    return m

frame = mat('Dark anodized bronze', (.075,.06,.044), .72)
brass = mat('Brushed champagne door trim', (.60,.39,.18), .75)
glass = mat('Clear blue-green glazing', (.49,.83,.82), .05,.19)
stone = mat('Warm limestone', (.62,.56,.46))
roof = mat('Ivory ceiling', (.85,.82,.74))

def surface(material, stem, roughness, relief):
    material.name = stem.replace('-', ' ')
    nodes = material.node_tree.nodes
    link = material.node_tree.links.new
    shader = nodes.get('Principled BSDF')
    base = bpy.data.images.load(str(out/'images'/f'{stem}.png'))
    color = nodes.new('ShaderNodeTexImage')
    color.image = base
    link(color.outputs['Color'], shader.inputs['Base Color'])
    w, h = base.size
    pixels = np.empty(w*h*4, dtype=np.float32)
    base.pixels.foreach_get(pixels)
    gray = pixels.reshape(h,w,4)[:,:,:3].mean(axis=2)
    detail = np.clip((gray-gray.mean()) / max(gray.std(), .01), -3, 3)
    dx = (np.roll(detail,1,1)-np.roll(detail,-1,1))*relief
    dy = (np.roll(detail,1,0)-np.roll(detail,-1,0))*relief
    normal = np.stack((dx,dy,np.ones_like(dx)), axis=2)
    normal /= np.linalg.norm(normal,axis=2,keepdims=True)
    for suffix in ('Roughness','Normal'):
        data = np.ones((h,w,4), dtype=np.float32)
        if suffix == 'Normal':
            data[:,:,:3] = normal*.5+.5
        else:
            data[:,:,:3] = np.clip(roughness-detail*.025,0,1)[:,:,None]
        im = bpy.data.images.new(f'{stem}-{suffix}',w,h,alpha=False)
        im.colorspace_settings.name = 'Non-Color'
        im.pixels.foreach_set(data.ravel())
        filename = f'{stem}-{suffix}.png'
        im.filepath_raw = str(out/'images'/filename)
        im.save()
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = im
        if suffix == 'Normal':
            convert = nodes.new('ShaderNodeNormalMap')
            link(tex.outputs['Color'],convert.inputs['Color'])
            link(convert.outputs['Normal'],shader.inputs['Normal'])
        else:
            link(tex.outputs['Color'],shader.inputs['Roughness'])

surface(stone,'Honed-terrazzo',.42,.045)
surface(roof,'Ivory-plaster',.86,.10)

def group(name):
    global collection
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)

def box(name, pos, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    for v in o.data.vertices:
        for i in range(3):
            v.co[i] *= size[i]
    o.data.materials.append(material)
    return o

group('01 Floors')
box('Dining floor',(0,-15,-.35),(100,70,.7),stone)
box('Kitchen floor',(0,35,-.35),(100,30,.7),stone)

def wall(name, side, fixed, door=False):
    group(name)
    def part(label, u, z, width, height, depth, material, offset=0):
        pos = (fixed+offset,u,z) if side else (u,fixed+offset,z)
        size = (depth,width,height) if side else (width,depth,height)
        return box(label,pos,size,material)
    span = 49.65 if side or fixed == 20 else 50
    def bays(a,b,n):
        w = (b-a)/n
        for i in range(n):
            mid = a+(i+.5)*w
            part('Fixed glass',mid,8,w-.26,15.48,.13,glass)
            if i:
                part('Glazing mullion',a+i*w,8,.26,16,.42,frame)
        for z in (.13,15.87):
            part('Perimeter rail',(a+b)/2,z,b-a,.26,.45,frame)
    if door:
        gap = 8 if fixed < 0 else 6
        bays(-span,-gap,5)
        bays(gap,span,5)
        for u in (-gap,gap):
            part('Portal jamb',u,8,.4,16,.56,brass)
        part('Door header',0,10.3,2*gap,.4,.56,brass)
        part('Portal transom',0,13.15,2*gap-.4,5.3,.13,glass)
        part('Portal crown',0,15.86,2*gap,.28,.5,brass)
        for sign in (-1,1):
            mid = sign*(gap/2+.08)
            w = gap-.3
            part('Door leaf glass',mid,5.1,w-.36,9.58,.16,glass)
            for u in (mid-w/2+.09,mid+w/2-.09):
                part('Door stile',u,5.1,.18,9.96,.32,brass)
            for z in (.23,9.97):
                part('Door rail',mid,z,w,.22,.32,brass)
            for face in (-1,1):
                for z in (3.45,5.85):
                    part('Pull mount',sign*.66,z,.16,.16,.52,brass,face*.29)
                part('Vertical pull',sign*.66,4.65,.18,2.72,.2,brass,face*.56)
    else:
        bays(-span,span,10)
    for u in (-span+.13,span-.13):
        part('End jamb',u,8,.26,16,.48,frame)

wall('02 Entrance facade',False,-49.7,True)
wall('03 Rear facade',False,49.7)
wall('04 West facade',True,-49.7)
wall('05 East facade',True,49.7)
wall('06 Kitchen glass partition',False,20,True)
group('07 Ceiling')
box('Full ceiling slab',(0,0,16.32),(100,100,.64),roof)

# Fit the glazing, portals, and ceiling to the finished clear height.
scene.unit_settings.system = 'METRIC'
for obj in scene.objects:
    if obj.users_collection[0].name != '01 Floors':
        obj.location.z *= 6 / 16
        for vertex in obj.data.vertices:
            vertex.co.z *= 6 / 16

for obj in scene.objects:
    if obj.active_material not in (stone,roof):
        continue
    mesh = obj.data
    uv = mesh.uv_layers.active.data
    repeat = 1.2 if obj.active_material == stone else .8
    for face in mesh.polygons:
        axes = [i for i in range(3) if abs(face.normal[i]) < .5]
        for loop in face.loop_indices:
            p = mesh.vertices[mesh.loops[loop].vertex_index].co + obj.location
            uv[loop].uv = (p[axes[0]]/repeat,p[axes[1]]/repeat)

from math import pi
import bmesh

steel = mat('Satin stainless steel', (.52,.56,.57), .85)
enamel = mat('Eucalyptus powder coat', (.13,.22,.19), .28)
liner = mat('Graphite cabinet liner', (.043,.053,.05), .35)
proxy_material = mat('Invisible collision geometry', (0,0,0), alpha=0)
group('08 Collision proxies - shell')
shell_objects = list(scene.objects)
proxy_meshes = {}

def collider(name, mesh, location, parent=None):
    if mesh not in proxy_meshes:
        proxy = mesh.copy()
        proxy.materials.clear()
        proxy.materials.append(proxy_material)
        proxy_meshes[mesh] = proxy
    obj = bpy.data.objects.new(name+'-colonly', proxy_meshes[mesh])
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.display_type = 'WIRE'

for obj in shell_objects:
    collider(obj.name,obj.data,obj.location)

cabinet_meshes = {}
walnut = mat('Walnut',(.23,.09,.04))
quartz = mat('Quartzite',(.8,.68,.52))
surface(walnut,'Walnut',.43,.045)
surface(quartz,'Quartzite',.33,.018)
def block_mesh(size, material, bevel):
    key = (size,material.name,bevel)
    if key in cabinet_meshes:
        return cabinet_meshes[key]
    bm = bmesh.new()
    vertices = bmesh.ops.create_cube(bm,size=1)['verts']
    for vert in vertices:
        for axis in range(3):
            vert.co[axis] *= size[axis]
    if bevel:
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES')
    mesh = bpy.data.meshes.new(material.name+' profile')
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    if material in (walnut,quartz):
        uv = mesh.uv_layers.new().data
        for face in mesh.polygons:
            axis = max(range(3), key=lambda i: abs(face.normal[i]))
            a,b = [(1,2),(0,2),(0,1)][axis]
            scale = 1.85 if material == quartz else 1.2
            for i in face.loop_indices:
                v = mesh.vertices[mesh.loops[i].vertex_index].co
                uv[i].uv = (.5+v[a]/scale,.5+v[b]/scale)
    cabinet_meshes[key] = mesh
    return mesh

from math import cos, sin

def cabinet(prefix, origin, assembly, upper, wash=False):
    label = prefix + ('_Upper' if upper else '_Base')
    root = bpy.data.objects.new(label,None)
    collection.objects.link(root)
    root.location = origin
    root.parent = assembly
    root.empty_display_size = .08
    owner = root
    offset = Vector((0,0,0))
    def panel(name, pos, size, material, bevel=.003):
        obj = bpy.data.objects.new(label+'_'+name,block_mesh(size,material,bevel))
        collection.objects.link(obj)
        obj.parent = owner
        obj.location = Vector(pos)-offset
        collider(obj.name,block_mesh(size,proxy_material,0),obj.location,owner)
    def tube(name, points, radius):
        points = list(map(Vector,points))
        verts, faces = [], []
        for i,p in enumerate(points):
            tangent = (points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
            side = Vector((1,0,0))
            normal = tangent.cross(side).normalized()
            for k in range(12):
                t = 2*pi*k/12
                verts.append(p+radius*(side*cos(t)+normal*sin(t)))
                if i:
                    a = (i-1)*12+k
                    b = (i-1)*12+(k+1)%12
                    faces.append((a,b,b+12,a+12))
        faces += [tuple(reversed(range(12))),tuple(range(len(verts)-12,len(verts)))]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts,[],faces)
        mesh.materials.append(steel)
        obj = bpy.data.objects.new(label+'_'+name,mesh)
        collection.objects.link(obj)
        obj.parent = root
        collider(obj.name,mesh,(0,0,0),root)
    if wash and upper:
        # The shallower wall rack leaves headroom over the bowls.
        for x in (-1.235,1.235):
            panel('RackEnd',(x,.39,1.95),(.03,.57,.70),walnut)
        for z in (1.65,2.14):
            for y in (.13,.65):
                panel('ShelfRail',(0,y,z),(2.46,.027,.035),steel)
            for i in range(41):
                x = -1.19+i*.0595
                panel('DryingSlat',(x,.39,z),(.009,.53,.011),steel)
                if z==1.65:
                    tube('PlateDivider',[(x,.23,z),(x,.28,z+.12),(x,.42,z+.12),(x,.48,z)],.004)
        panel('DripTray',(0,.39,1.61),(2.45,.55,.018),steel)
        return
    bottom, top = (1.60,2.44) if upper else (.15,.92)
    height = top-bottom
    mid = (top+bottom)/2
    width = 2.5 if wash else 1.8
    panel('Back',(0,.658,mid),(width-.04,.02,height-.025),walnut)
    for name,z in [('Deck',bottom+.012),('Shelf',mid),('Cap',top-(.013 if upper else .054))]:
        if not wash or name=='Deck':
            panel(name,(0,.025,z),(width-.04,1.25,.024),walnut)
    for side,x in [('L',-.5*width+.008),('R',.5*width-.008)]:
        panel('End_'+side,(x,.01,mid-(0 if upper else .018)),(.016,1.37,height-(.008 if upper else .044)),walnut)
    fronts = [('Left',-width/4+.005,mid,width/2-.02,height-.025),('Right',width/4-.005,mid,width/2-.02,height-.025)]
    for name,x,z,w,h in fronts:
        if not upper:
            h -= .04
            z -= .02
        offset = Vector((x+(-w/2 if x<0 else w/2),-.65,z))
        owner = bpy.data.objects.new(label+'_Hinge_'+name,None)
        collection.objects.link(owner)
        owner.parent = root
        owner.location = offset
        owner.empty_display_size = .035
        panel(name+'_Front',(x,-.633,z),(w,.034,h),walnut,.005)
        grip_z = z-h/2+.065 if upper else z+h/2-.065
        grip_x = x*.43 if len(fronts)==2 else 0
        for end,delta in [('L',-.115),('R',.115)]:
            panel(name+'_PullFoot'+end,(grip_x+delta,-.668,grip_z),(.017,.036,.018),brass)
        panel(name+'_Pull',(grip_x,-.69,grip_z),(.25,.02,.023),brass,.005)
    owner = root
    offset = Vector((0,0,0))
    if not upper:
        if wash:
            # Two open bowls share a steel bridge and a rear faucet deck.
            for name,y,depth in [('Front',-.625,.15),('Rear',.45,.50)]:
                panel(name+'Deck',(0,y,.902),(2.5,depth,.036),steel)
            for x,w in [(-.99,.52),(0,.06),(.99,.52)]:
                panel('Drainboard',(x,-.175,.902),(w,.75,.036),steel)
            for x in (-.38,.38):
                panel('BowlBase',(x,-.175,.64),(.70,.75,.014),steel)
                for dx in (-.345,.345):
                    panel('BowlSide',(x+dx,-.175,.765),(.01,.75,.25),steel)
                for y in (-.545,.195):
                    panel('BowlWall',(x,y,.765),(.7,.01,.25),steel)
                bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.045,depth=.004)
                drain=bpy.context.object
                drain.name=label+'_DrainStrainer'
                drain.parent=root
                drain.location=(x,-.175,.649)
                drain.data.materials.append(liner)
            arc=[(-.38,.12+.16*cos(i*pi/16),1.19+.16*sin(i*pi/16)) for i in range(17)]
            tube('MixerSpout',[(-.38,.28,.92)]+arc+[(-.38,-.04,1.15)],.021)
            panel('MixerLever',(-.325,.28,1.01),(.11,.027,.025),steel)
        else:
            panel('Worktop',(0,0,.92-.018),(width,1.4,.036),quartz,.006)
        for x,end in [(-width/2+.12,'L'),(width/2-.12,'R')]:
            for y,side in [(-.53,'Front'),(.53,'Rear')]:
                pos = (x,y,.075)
                size = (.055,.055,.15)
                panel(end+side+'_Leg',pos,size,steel,.006)

for wall_name,centers,angle in [
    ('North',[i*12.9 for i in range(-3,4)],0),
    ('West',[26.4,39.3],pi/2),
    ('East',[26.4,39.3],-pi/2),
]:
    group('09 Cabinetry - '+wall_name)
    for run,center in enumerate(centers,1):
        origin = (center,48.6,0) if wall_name=='North' else ((-48.6 if wall_name=='West' else 48.6),center,0)
        prefix = f'Kitchen_{wall_name}_{run:02}'
        assembly=bpy.data.objects.new(prefix,None)
        collection.objects.link(assembly)
        assembly.location=origin
        assembly.rotation_euler.z=angle
        for name,x in [('Cab01',-3.05),('Cab02',-1.25),('Cab03',.55),('Wash',2.70)]:
            for upper in (False,True):
                cabinet(prefix+'_'+name,(x,0,0),assembly,upper,name=='Wash')

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        s = area.spaces.active
        s.shading.type = 'MATERIAL'
        s.overlay.show_overlays = False
        s.region_3d.view_rotation = Vector((.32,1,.035)).to_track_quat('-Z','Y')
        s.region_3d.view_location = (0,0,7)
        s.region_3d.view_distance = 144
bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version = 0
for image in bpy.data.images:
    if image.filepath:
        image.filepath_raw = '//images/' + Path(image.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'),relative_remap=False)
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'),export_format='GLB')
for filename,prefix in [('Cabinets','Kitchen_'),('CabinetPanelGroup','Kitchen_North_01')]:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in scene.objects:
        if obj.name.startswith(prefix):
            obj.select_set(True)
    if filename == 'CabinetPanelGroup':
        scene.objects[prefix].location = (0,0,0)
    bpy.ops.export_scene.gltf(filepath=str(out/(filename+'.glb')),use_selection=True)
