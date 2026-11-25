import bpy
import bmesh
from math import pi, sin, cos, radians
from pathlib import Path
from mathutils import Vector

out = Path(bpy.data.filepath).parent
scene = bpy.context.scene
previous=bpy.data.collections.get('10 Commercial appliances')
if previous:
    for item in list(previous.objects):
        bpy.data.objects.remove(item,do_unlink=True)
    bpy.data.collections.remove(previous)
collection = bpy.data.collections.new('10 Commercial appliances')
scene.collection.children.link(collection)

def finish(name, rgb, metal, rough, glow=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb,1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    for key,val in [('Base Color',(*rgb,1)),('Metallic',metal),('Roughness',rough),
                    ('Emission Color',(*rgb,1)),('Emission Strength',glow)]:
        p.inputs[key].default_value = val
    return m

steel = finish('Appliance | satin stainless',(.58,.61,.62),.86,.29)
polish = finish('Appliance | polished steel',(.72,.74,.75),.95,.19)
interior = finish('Appliance | satin liner',(.69,.72,.70),.56,.38)
iron = finish('Appliance | cast iron',(.042,.045,.047),.48,.67)
rubber = finish('Appliance | charcoal gasket',(.018,.021,.024),.04,.63)
glass = finish('Appliance | smoked enamel',(.028,.044,.049),.48,.14)
brass = finish('Appliance | burner brass',(.50,.32,.105),.8,.38)
led = finish('Appliance | cool indicator',(.48,.91,.84),.05,.35,1.2)
amber = finish('Appliance | amber indicator',(.94,.30,.045),.05,.3,.8)
wood = bpy.data.materials.get('Walnut') or iron
proxy = bpy.data.materials['Invisible collision geometry']
cache = {}

def obj(name,mesh,parent,pos):
    o = bpy.data.objects.new(name,mesh)
    collection.objects.link(o)
    o.parent = parent
    o.location = pos
    if mesh is None:
        o.empty_display_size=.08
    return o

def box(name,pos,size,m=steel,parent=None,edge=.005):
    key = (size,m.name,edge)
    if key not in cache:
        bm = bmesh.new()
        vs=bmesh.ops.create_cube(bm,size=1)['verts']
        for v in vs:
            for i in range(3):
                v.co[i]*=size[i]
        if edge:
            bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(edge,min(size)*.32),
                            segments=3,affect='EDGES')
        mesh=bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(m)
        cache[key]=mesh
    return obj(name,cache[key],parent,pos)

def rod(name,a,b,r,m,parent,n=24):
    a,b=Vector(a),Vector(b)
    length=(b-a).length
    key=('round',round(length,6),r,m.name,n)
    if key not in cache:
        bm=bmesh.new()
        bmesh.ops.create_cone(bm,cap_ends=True,segments=n,radius1=r,radius2=r,depth=length)
        mesh=bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for f in mesh.polygons:
            f.use_smooth=len(f.vertices)==4
        mesh.materials.append(m)
        cache[key]=mesh
    o=obj(name,cache[key],parent,(a+b)/2)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def collision(name,pos,size,parent):
    o=box(name+'-colonly',pos,size,proxy,parent,0)
    o.display_type='WIRE'

def feet(root,w,d,h):
    for x in (-w/2+.10,w/2-.10):
        for y in (-d/2+.09,d/2-.09):
            rod('AdjustableFoot',(x,y,.012),(x,y,h),.033,steel,root)
            rod('FootPad',(x,y,0),(x,y,.02),.043,rubber,root)

def refrigerator():
    p=obj('DoubleDoorRefrigerator',None,None,(0,0,0))
    feet(p,1.86,.94,.15)
    for x in (-.90,.90):
        box('InsulatedSide',(x,0,1.16),(.06,.94,2.02),steel,p)
    box('RearLiner',(0,.44,1.16),(1.74,.06,2.02),interior,p)
    for z in (.19,1.98):
        box('InsulatedDeck',(0,0,z),(1.8,.94,.08),interior,p)
    box('CentreMullion',(0,-.435,1.08),(.045,.065,1.74),steel,p)
    for x in (-.443,.443):
        for y in (-.35,.35):
            for dx in (-.39,.39):
                box('ShelfStandard',(x+dx,y,1.08),(.015,.024,1.63),polish,p)
        for z in (.48,.83,1.18,1.53):
            for y in (-.35,.35):
                rod('ShelfFrame',(x-.402,y,z),(x+.402,y,z),.009,polish,p)
            for i in range(18):
                xx=x-.40+i*.80/17
                rod('ShelfWire',(xx,-.35,z),(xx,.35,z),.0048,interior,p,12)
        rod('EvaporatorCover',(x,.386,1.76),(x,.408,1.76),.12,steel,p)
        for i in range(-4,5):
            width=(.103**2-(i*.021)**2)**.5
            box('AirReturn',(x,.383,1.76+i*.021),(2*width,.006,.008),rubber,p)
        box('InteriorLight',(x,0,1.933),(.42,.024,.009),led,p)
    box('CompressorHeader',(0,0,2.11),(1.86,.94,.26),steel,p)
    box('IntakeRecess',(-.23,-.474,2.11),(1.23,.009,.177),rubber,p)
    for i in range(7):
        box('VentLouver',(-.23,-.488,2.043+i*.022),(1.20,.024,.010),steel,p)
    box('Controller',(.65,-.479,2.11),(.32,.02,.117),glass,p)
    # Seven-segment temperature readout.
    for j,segments in enumerate(('abcdef','abdeg')):
        for seg in segments:
            x,z,w,h={'a':(0,.027,.029,.004),'b':(.015,.014,.004,.023),
                     'c':(.015,-.014,.004,.023),'d':(0,-.027,.029,.004),
                     'e':(-.015,-.014,.004,.023),'f':(-.015,.014,.004,.023),
                     'g':(0,0,.029,.004)}[seg]
            box('DisplaySegment',(.60+j*.045+x,-.491,2.11+z),(w,.002,h),led,p)
    for sign,side in [(-1,'Left'),(1,'Right')]:
        hinge=obj(side+'DoorHinge',None,p,(sign*.912,-.49,.22))
        hinge.rotation_euler.z=sign*radians(103)
        cx=-sign*.448
        box(side+'Door',(cx,-.027,.856),(.894,.074,1.712),steel,hinge,.014)
        box('MagneticGasket',(cx,.014,.856),(.86,.015,1.68),rubber,hinge)
        box('EmbossedInnerPanel',(cx,.025,.856),(.823,.024,1.635),interior,hinge,.014)
        for z in (.30,.78):
            box('DoorBinBase',(cx,.085,z),(.72,.12,.022),interior,hinge)
            for dx in (-.35,.35):
                box('BinCheek',(cx+dx,.085,z+.042),(.015,.12,.09),steel,hinge)
            rod('BinGuard',(cx-.35,.14,z+.085),(cx+.35,.14,z+.085),.009,polish,hinge)
        gx=-sign*.81
        for z in (.65,1.22):
            rod('PullStandoff',(gx,-.063,z),(gx,-.122,z),.016,steel,hinge)
        rod('VerticalPull',(gx,-.122,.63),(gx,-.122,1.24),.019,polish,hinge)
        collision(side+'Door',(cx,0,.856),(.894,.10,1.712),hinge)
    for side,x in [('Left',-.90),('Right',.90)]:
        collision(side+'Side',(x,0,1.16),(.06,.94,2.02),p)
    collision('Rear',(0,.44,1.16),(1.74,.06,2.02),p)
    collision('Base',(0,0,.19),(1.8,.94,.08),p)
    collision('Header',(0,0,2.09),(1.86,.94,.30),p)
    return p

def knob(p,x,y,z):
    rod('ControlBezel',(x,y,z),(x,y-.012,z),.035,polish,p)
    rod('RotaryKnob',(x,y-.012,z),(x,y-.046,z),.028,iron,p)
    box('KnobIndex',(x,y-.047,z+.017),(.004,.004,.012),interior,p)

def range_oven():
    p=obj('FiveBurnerOvenRange',None,None,(0,0,0))
    feet(p,1.20,.90,.15)
    box('OvenChassis',(0,0,.51),(1.20,.90,.72),steel,p,.014)
    box('OvenDoorSeal',(0,-.455,.48),(1.10,.028,.51),rubber,p)
    box('DoorSurround',(0,-.478,.48),(1.07,.032,.485),steel,p)
    box('ObservationWindow',(0,-.499,.475),(.82,.013,.292),glass,p,.015)
    for x in (-.46,.46):
        rod('HandlePost',(x,-.49,.68),(x,-.55,.68),.018,steel,p)
    rod('DoorPull',(-.49,-.55,.68),(.49,-.55,.68),.021,polish,p)
    for x in (-.48,-.30,-.12,.06,.24,.46):
        knob(p,x,-.454,.804)
    box('PilotIndicator',(.53,-.458,.804),(.016,.006,.014),amber,p)
    box('HobWell',(0,0,.872),(1.18,.88,.025),iron,p)
    box('RearUpstand',(0,.431,.944),(1.20,.026,.16),steel,p)
    for x,y,r in [(-.39,-.22,.070),(.39,-.22,.080),(-.39,.20,.083),(.39,.20,.063),(0,0,.106)]:
        rod('BurnerCrown',(x,y,.887),(x,y,.907),r,brass,p,48)
        rod('BurnerCap',(x,y,.907),(x,y,.917),r*.88,iron,p,48)
        for i in range(4):
            a=i*pi/2
            grate=box('PanSupport',(x+.132*cos(a),y+.132*sin(a),.926),(.114,.022,.031),iron,p)
            grate.rotation_euler.z=a
    for x in (-.57,-.20,.20,.57):
        box('GrateRunner',(x,0,.915),(.018,.84,.022),iron,p)
    for y in (-.412,0,.412):
        box('GrateCrossbar',(0,y,.915),(1.15,.018,.022),iron,p)
    extraction_hood(p,1.4/3.96)
    collision('OvenBody',(0,0,.54),(1.20,.90,.78),p)
    return p

def grill():
    p=obj('CommercialKebabGrill',None,None,(0,0,0))
    feet(p,3.60,.70,.78)
    for y in (-.26,.26):
        rod('CentreLeg',(0,y,0),(0,y,.78),.035,steel,p)
    for z in (.22,.78):
        box('StandShelf',(0,0,z),(3.56,.67,.033),steel,p)
    box('Firebox',(0,0,.84),(3.60,.7,.17),steel,p,.012)
    box('HeatBed',(0,0,.933),(3.52,.63,.025),iron,p)
    for i in range(45):
        x=(i-22)*.077
        bar=box('HeatDiffuser',(x,0,.95),(.046,.56,.046),iron,p)
        bar.rotation_euler.y=pi/4
    for y in (-.309,.309):
        box('SkewerRest',(0,y,1.011),(3.57,.021,.044),steel,p)
    for x in (-1.787,1.787):
        box('WindGuard',(x,0,.984),(.021,.69,.12),steel,p)
    for i in range(24):
        x=(i-11.5)*.146
        box('FlatSkewer',(x,-.015,1.037),(.015,.79,.004),polish,p,.001)
        rod('SkewerGrip',(x,-.402,1.037),(x,-.55,1.037),.014,iron,p)
    for x in (-1.45,-.87,-.29,.29,.87,1.45):
        knob(p,x,-.35,.849)
    for x in (-1.16,0,1.16):
        box('DripDrawer',(x,-.35,.758),(1.12,.02,.055),steel,p)
        box('DripDrawerPull',(x,-.379,.76),(.22,.033,.015),iron,p)
    collision('GrillHead',(0,0,.90),(3.60,.70,.28),p)
    collision('Shelf',(0,0,.22),(3.56,.67,.033),p)
    extraction_hood(p,1.0)
    return p

def extraction_hood(p,width_scale):
    hood=obj('ExtractionHood',None,p,(0,0,0))
    for y in (-.605,.605):
        box('CanopyFascia',(0,y,2.39),(3.96,.04,.38),steel,hood)
    for x in (-1.96,1.96):
        box('CanopyEnd',(x,0,2.39),(.04,1.20,.38),steel,hood)
    for x in (-1.80,1.80):
        for y in (-.48,.48):
            rod('SuspensionRod',(x,y,2.55),(x,y,6.0),.012,polish,hood)
    for i in range(6):
        x=(i-2.5)*.635
        box('FilterCassette',(x,0,2.48),(.613,.88,.04),iron,hood)
        for k in range(11):
            blade=box('GreaseBaffle',(x+(k-5)*.054,0,2.45),(.035,.85,.025),steel,hood)
            blade.rotation_euler.y=.30
    for x in (-1.2,0,1.2):
        box('HoodLamp',(x,-.52,2.42),(.44,.045,.012),led,hood)
    # Form the sheet-metal transition and open duct using connected perimeter rings.
    n=64
    verts=[]
    for level,r in [(2.58,None),(2.98,.30),(6.81,.30),(6.81,.285),(2.98,.285),(2.58,None)]:
        for k in range(n):
            a=2*pi*k/n+pi/4
            u,v=cos(a),sin(a)
            if r is None:
                verts.append((1.98*u/max(abs(u),abs(v)),.625*v/max(abs(u),abs(v)),level))
            else:
                verts.append((r*u,r*v,level))
    faces=[(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for j in range(5) for k in range(n)]
    mesh=bpy.data.meshes.new('Open exhaust duct')
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(steel)
    obj('CanopyTransitionAndDuct',mesh,hood,(0,0,0))
    for z in (3,4.4,5.8,6.28,6.79):
        bpy.ops.mesh.primitive_torus_add(major_radius=.303,minor_radius=.012,major_segments=64,minor_segments=8)
        band=bpy.context.object
        for c in list(band.users_collection):
            c.objects.unlink(band)
        collection.objects.link(band)
        band.name='DuctCollar'
        band.parent=hood
        band.location=(0,0,z)
        band.data.materials.append(polish)
    for x in (-.23,.23):
        rod('CowlStay',(x,0,6.78),(x,0,6.99),.012,steel,hood)
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=.43,radius2=.08,depth=.13)
    cap=bpy.context.object
    for c in list(cap.users_collection):
        c.objects.unlink(cap)
    collection.objects.link(cap)
    cap.name='RoofExhaustRainCap'
    cap.parent=hood
    cap.location=(0,0,7.04)
    cap.data.materials.append(steel)
    collision('Canopy',(0,0,2.43),(3.96,1.25,.46),hood)
    collision('ExhaustRiser',(0,0,4.89),(.6,.6,3.84),hood)
    hood.scale.x=width_scale

def export_asset(root):
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root,*root.children_recursive]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/(root.name+'.glb')),use_selection=True)

fridge=refrigerator()
oven=range_oven()
kebab=grill()
for asset in (fridge,oven,kebab):
    export_asset(asset)

def linked_copy(root,index):
    mapping={}
    for source in [root,*root.children_recursive]:
        duplicate=source.copy()
        collection.objects.link(duplicate)
        mapping[source]=duplicate
    for source,duplicate in mapping.items():
        duplicate.parent=mapping.get(source.parent)
        if source.name.endswith('-colonly'):
            duplicate.name=source.name[:-8]+f'_{index}-colonly'
    mapping[root].name=f'{root.name}_{index:02}'
    return mapping[root]


source=bpy.data.objects['Kitchen_North_01']
for root in [item for item in scene.objects if item.parent is None]:
    if root.parent is None and root != source and root.name.startswith(('Kitchen_North_', 'Kitchen_West_', 'Kitchen_East_', 'CentreIsland')):
        for part in reversed(list(root.children_recursive)):
            bpy.data.objects.remove(part,do_unlink=True)
        bpy.data.objects.remove(root,do_unlink=True)
for part in list(source.children):
    if '_Cab01_' in part.name or '_Cab02_' in part.name:
        for child in reversed(list(part.children_recursive)):
            bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(part,do_unlink=True)
source.location=(0,0,0)
source.rotation_euler.z=0
for part in [source,*source.children_recursive]:
    part.hide_render=False
    part.hide_set(False)
group=linked_copy(source,1)
group.name='CabinetPanelGroup'
oven.parent=group
oven.location=(-1.08,0,0)
export_asset(group)
# Keep the cabinet template available for rebuilding without adding a visible unit.
for part in [source,*source.children_recursive]:
    part.use_fake_user=True
    for owning_collection in list(part.users_collection):
        owning_collection.objects.unlink(part)
placements=[(-18,48.6,0),(18,48.6,0)]
for x,angle in [(-48.6,pi/2),(48.6,-pi/2)]:
    placements.extend((x,y,angle) for y in (30,39))
placements.extend((x,36,pi/2 if x<0 else -pi/2) for x in (-18,-7,7,18))
groups=[group]+[linked_copy(group,i) for i in range(2,11)]
vents=[]
for unit,(x,y,angle) in zip(groups,placements):
    unit.location=(x,y,0)
    unit.rotation_euler.z=angle
    vents.append((x-1.08*cos(angle),y-1.08*sin(angle)))
for i,(cold,hot,angle) in enumerate([
    ((-37,48.3),(37,48.3),0),
    ((-48.3,25),(-48.3,45.5),pi/2),
    ((48.3,25),(48.3,45.5),-pi/2)
]):
    for asset,pos in [(fridge,cold),(kebab,hot)]:
        unit=linked_copy(asset,i+1) if i else asset
        unit.location=(*pos,0)
        unit.rotation_euler.z=angle
    vents.append(hot)
for vx,vy in vents:
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.305,depth=1.5,
        location=(vx,vy,6.15))
    cutter=bpy.context.object
    for name in ('Full ceiling slab','Full ceiling slab-colonly'):
        slab=bpy.data.objects[name]
        bpy.context.view_layer.objects.active=slab
        mod=slab.modifiers.new('Exhaust penetration','BOOLEAN')
        mod.object=cutter
        mod.operation='DIFFERENCE'
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Restaurant.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'Restaurant.glb'))


