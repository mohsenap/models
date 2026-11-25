import bpy
import numpy as np
from math import sin, cos, pi, sqrt
from pathlib import Path
from mathutils import Vector

out=Path(bpy.data.filepath).parent
walnut=bpy.data.materials['Walnut']
stone=bpy.data.materials['Quartzite']
brass=bpy.data.materials['Brushed champagne door trim']
for material in (walnut,stone,brass):
    material.use_fake_user=True
# Work in memory from the restaurant's material library.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
def finish(name,rgb,rough,metal=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    return m

bronze=finish('Smoked bronze',(.115,.075,.045),.34,.80)
welt=finish('Moss velvet piping',(.085,.113,.064),.66)
cloth=finish('Olive mohair basket weave',(.18,.23,.12),.78)
p=cloth.node_tree.nodes.get('Principled BSDF')
p.inputs['Sheen Weight'].default_value=.32
# Seamless crossing warp and weft yarns, with a corresponding tangent normal.
n=512
y,x=np.mgrid[0:n,0:n]/n*32
a,b=np.sin(pi*x)**2,np.sin(pi*y)**2
warp=(np.floor(x)+np.floor(y))%2
h=np.where(warp,a*(.48+.52*b),b*(.48+.52*a))
noise=np.random.default_rng(38).normal(0,.045,h.shape)
dy,dx=np.gradient(h)
for suffix in ('Color','Normal'):
    im=bpy.data.images.new('MossWeave-'+suffix,n,n,alpha=False)
    rgba=np.ones((n,n,4),np.float32)
    if suffix=='Color':
        rgba[:,:,:3]=(.63+.38*h+noise)[:,:,None]*np.array([.173,.209,.121])
    else:
        im.colorspace_settings.name='Non-Color'
        vec=np.stack((-dx,-dy,np.ones_like(h)),axis=2)
        rgba[:,:,:3]=vec/np.linalg.norm(vec,axis=2)[:,:,None]*.5+.5
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw=str(out/'images'/(im.name+'.png'))
    im.save()
    tex=cloth.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=im
    if suffix=='Color':
        cloth.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    else:
        nm=cloth.node_tree.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value=.50
        cloth.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color'])
        cloth.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])

def asset(name):
    global root
    root=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(root)
    return root

def loft(name,rings,mat,period=1):
    m=len(rings[0])
    faces=[tuple(reversed(range(m)))]
    for j in range(len(rings)-1):
        for i in range(m):
            a=j*m+i
            b=j*m+(i+1)%m
            faces.append((a,b,b+m,a+m))
    end=(len(rings)-1)*m
    faces.append(tuple(range(end,end+m)))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([v for row in rings for v in row],[],faces)
    mesh.update()
    uv=mesh.uv_layers.new().data
    for face in mesh.polygons:
        face.use_smooth=face.index not in (0,len(faces)-1)
        axis=max(range(3),key=lambda k:abs(face.normal[k]))
        a,b=[(1,2),(0,2),(0,1)][axis]
        for i in face.loop_indices:
            v=mesh.vertices[mesh.loops[i].vertex_index].co
            uv[i].uv=(.5+v[a]/period,.5+v[b]/period)
    o=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.parent=root
    mesh.materials.append(mat)
    return o

def outline(w,d,r):
    result=[]
    for cx,cy,angle in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
        for i in range(13):
            t=(angle+i*90/12)*pi/180
            result.append((cx+r*cos(t),cy+r*sin(t)))
    return result

def slab(name,shape,rows,mat,period=1):
    return loft(name,[[(x*s,y*s,z) for x,y in shape] for z,s in rows],mat,period)

def shaft(name,a,b,r1,r2,mat):
    a,b=Vector(a),Vector(b)
    axis=(b-a).normalized()
    u=axis.cross(Vector((0,1,0))).normalized()
    v=axis.cross(u)
    loft(name,[[pos+r*(u*cos(i*pi/12)+v*sin(i*pi/12)) for i in range(24)]
               for pos,r in [(a,r1),(b,r2)]],mat)

def export():
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root,*root.children_recursive]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/(root.name+'.glb')),use_selection=True)

chair=asset('SaloonDiningChair')
seat=outline(.51,.48,.105)
slab('Walnut seat frame',seat,[(.369,.89),(.375,.95),(.402,.99),(.408,.97)],walnut)
slab('Tailored seat cushion',seat,[(.400,.94),(.407,.99),(.431,1),(.452,.96),(.462,.84),(.465,.62)],cloth,.12)
slab('Seat edge welt',seat,[(.415,.995),(.418,1.003),(.421,.996)],welt)
for sx in (-1,1):
    for sy in (-1,1):
        foot=Vector((sx*.239,sy*.218,.0))
        hip=Vector((sx*.184,sy*.158,.385))
        join=foot.lerp(hip,.107)
        shaft('Champagne foot ferrule',foot,join,.012,.014,brass)
        shaft('Tapered walnut leg',join,hip,.014,.025,walnut)
    shaft('Raked back stile',(sx*.181,.16,.378),(sx*.199,.182,.741),.022,.018,walnut)

# A curved upholstered back wraps forward at the shoulders.
def backring(t):
    row=[]
    for i in range(96):
        a=2*pi*i/96
        bend=.249*cos(a)
        depth=.232-.140*(bend/.249)**2+.025*sin(a)+.025*t
        z=.566+.233*t+.023*(1-(bend/.249)**2)
        row.append((bend,depth,z))
    return row
rings=[backring(t) for t in (0,.035,.12,.84,.96,1)]
for ring,scale in zip(rings,(.945,.977,1,1,.978,.94)):
    for i,(x,y,z) in enumerate(ring):
        ring[i]=(x*scale,y,z)
loft('Crescent upholstered backrest',rings,cloth,.12)
export()

for circular in (False,True):
    asset('SaloonRoundTableForTwo' if circular else 'SaloonRectangularTableForTwo')
    shape=([( .45*cos(i*pi/64),.45*sin(i*pi/64)) for i in range(128)]
           if circular else outline(.95,.76,.055))
    slab('Honed quartzite dining surface',shape,[(.734,.987),(.738,1),(.754,1),(.760,.988)],stone,1.4)
    slab('Walnut undercut edge',shape,[(.707,.92),(.714,.956),(.734,.983)],walnut)
    slab('Fine brass edge band',shape,[(.732,.981),(.735,.985)],brass)
    def pedestal(name,profile,mat,flutes=False):
        rings=[]
        for z,r in profile:
            row=[]
            for i in range(256):
                a=2*pi*i/256
                rr=r+(.004*cos(32*a) if flutes else 0)
                row.append((rr*cos(a),rr*sin(a),z))
            rings.append(row)
        loft(name,rings,mat)
    pedestal('Weighted bronze foot',[(0,.244),(.006,.262),(.019,.262),(.027,.247),(.041,.151),(.052,.102)],bronze)
    pedestal('Lower brass collar',[(.047,.103),(.063,.104),(.068,.10)],brass)
    pedestal('Reeded walnut pedestal',[(.063,.096),(.09,.096),(.32,.075),(.49,.075),(.66,.095),(.688,.104)],walnut,True)
    pedestal('Upper brass collar',[(.681,.109),(.694,.11)],brass)
    pedestal('Top mounting plate',[(.694,.105),(.707,.163),(.715,.163)],bronze)
    export()
