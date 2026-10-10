import bpy, sys, math, random
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
MOTIF=argv[0]; OUT=argv[1]; SAMPLES=int(argv[2]) if len(argv)>2 else 160
HDRI="/tmp/claude-0/-home-user/ac9fbba0-b7d8-549e-a973-5b994798652b/scratchpad/dl/studio.hdr"
CYAN=(0.0,0.706,1.0); MAG=(0.82,0.0,1.0)
def srgb(c): return tuple(((x/12.92) if x<=0.04045 else ((x+0.055)/1.055)**2.4) for x in c)+(1,)
CY=srgb(CYAN); MG=srgb(MAG)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'
sc.cycles.samples=SAMPLES; sc.cycles.use_denoising=True; sc.cycles.denoiser='OPENIMAGEDENOISE'
sc.cycles.caustics_reflective=True; sc.cycles.caustics_refractive=True; sc.cycles.blur_glossy=0.5
sc.cycles.max_bounces=16; sc.cycles.transmission_bounces=16; sc.cycles.glossy_bounces=8; sc.cycles.transparent_max_bounces=16
sc.render.resolution_x=1200; sc.render.resolution_y=630; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'; sc.render.image_settings.quality=92
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Punchy'; sc.view_settings.exposure=0.45
sc.render.film_transparent=False

# ---------- world: HDRI studio + brand gradient backdrop plane
w=bpy.data.worlds.new("W"); sc.world=w; w.use_nodes=True; nt=w.node_tree; nt.nodes.clear()
env=nt.nodes.new("ShaderNodeTexEnvironment"); env.image=bpy.data.images.load(HDRI)
mp=nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value=(0,0,math.radians(35))
tc=nt.nodes.new("ShaderNodeTexCoord"); bg=nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value=0.9
lp=nt.nodes.new("ShaderNodeLightPath"); mix=nt.nodes.new("ShaderNodeMixShader")
dark=nt.nodes.new("ShaderNodeBackground"); dark.inputs["Color"].default_value=(0.004,0.006,0.012,1); dark.inputs["Strength"].default_value=1
out=nt.nodes.new("ShaderNodeOutputWorld")
L=nt.links; L.new(tc.outputs["Generated"],mp.inputs["Vector"]); L.new(mp.outputs["Vector"],env.inputs["Vector"]); L.new(env.outputs["Color"],bg.inputs["Color"])
L.new(lp.outputs["Is Camera Ray"],mix.inputs["Fac"]); L.new(bg.outputs[0],mix.inputs[1]); L.new(dark.outputs[0],mix.inputs[2]); L.new(mix.outputs[0],out.inputs["Surface"])

def mat(name):
    m=bpy.data.materials.new(name); m.use_nodes=True; n=m.node_tree.nodes; b=n["Principled BSDF"]; return m,b,m.node_tree
def imperfect(tree,b,scale=40,strength=0.035,base=0.06):
    """микро-царапины и пыль: шумовая карта шероховатости + лёгкий бамп"""
    n=tree.nodes; tx=n.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value=scale; tx.inputs["Detail"].default_value=8; tx.inputs["Roughness"].default_value=0.7
    cr=n.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value=0.35; cr.inputs["From Max"].default_value=0.75
    cr.inputs["To Min"].default_value=max(0,base-strength); cr.inputs["To Max"].default_value=base+strength
    tree.links.new(tx.outputs["Fac"],cr.inputs["Value"]); tree.links.new(cr.outputs["Result"],b.inputs["Roughness"])
    bp=n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value=0.02; bp.inputs["Distance"].default_value=0.002
    tx2=n.new("ShaderNodeTexNoise"); tx2.inputs["Scale"].default_value=scale*3; tx2.inputs["Detail"].default_value=10
    tree.links.new(tx2.outputs["Fac"],bp.inputs["Height"]); tree.links.new(bp.outputs["Normal"],b.inputs["Normal"])
def glass(tint=(1,1,1),rough=0.02,ior=1.5):
    m,b,t=mat("glass"); b.inputs["Base Color"].default_value=tint+(1,); b.inputs["Transmission Weight"].default_value=1.0; b.inputs["IOR"].default_value=ior
    b.inputs["Roughness"].default_value=rough; b.inputs["Coat Weight"].default_value=0.6; b.inputs["Coat Roughness"].default_value=0.03
    imperfect(t,b,scale=25,strength=0.02,base=rough); return m
def chrome(rough=0.08):
    m,b,t=mat("chrome"); b.inputs["Base Color"].default_value=(0.92,0.94,0.97,1); b.inputs["Metallic"].default_value=1; b.inputs["Roughness"].default_value=rough
    b.inputs["Coat Weight"].default_value=0.3; imperfect(t,b,scale=60,strength=0.04,base=rough); return m
def neon(col,strength=18):
    m,b,t=mat("neon"); b.inputs["Base Color"].default_value=col; b.inputs["Emission Color"].default_value=col; b.inputs["Emission Strength"].default_value=strength; b.inputs["Roughness"].default_value=0.3; return m
def floor_mat():
    m,b,t=mat("floor"); b.inputs["Base Color"].default_value=(0.012,0.014,0.02,1); b.inputs["Metallic"].default_value=0.2; b.inputs["Roughness"].default_value=0.22
    b.inputs["Coat Weight"].default_value=1.0; b.inputs["Coat Roughness"].default_value=0.05; imperfect(t,b,scale=4,strength=0.06,base=0.24)
    # неоновая сетка в цвете бренда (тонкая, слабая)
    n=t.nodes; tc=n.new("ShaderNodeTexCoord"); mp=n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value=(1.0,1.0,1.0)
    br=n.new("ShaderNodeTexBrick"); br.inputs["Mortar Size"].default_value=0.012; br.inputs["Scale"].default_value=1; br.offset=0; br.inputs["Color1"].default_value=(0,0,0,1); br.inputs["Color2"].default_value=(0,0,0,1); br.inputs["Mortar"].default_value=CY
    t.links.new(tc.outputs["Object"],mp.inputs["Vector"]); t.links.new(mp.outputs["Vector"],br.inputs["Vector"])
    mth=n.new("ShaderNodeMath"); mth.operation='MULTIPLY'; mth.inputs[1].default_value=2.0
    t.links.new(br.outputs["Color"],b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value=0.07
    return m

def add(obj,m,smooth=True,shadow_caustic=False):
    obj.data.materials.append(m)
    if smooth: 
        for p in obj.data.polygons: p.use_smooth=True
    obj.is_shadow_catcher=False
    if shadow_caustic: obj.cycles.is_caustics_caster=True
    return obj
def prim(fn,**k):
    fn(**k); return bpy.context.object
def sphere(loc,r,m,seg=96): o=prim(bpy.ops.mesh.primitive_uv_sphere_add,location=loc,radius=r,segments=seg,ring_count=seg//2); return add(o,m,shadow_caustic=True)
def cyl(loc,r,d,m,rot=(0,0,0),v=96): o=prim(bpy.ops.mesh.primitive_cylinder_add,location=loc,radius=r,depth=d,vertices=v,rotation=rot); return add(o,m,shadow_caustic=True)
def torus(loc,R,r,m,rot=(0,0,0)): o=prim(bpy.ops.mesh.primitive_torus_add,location=loc,major_radius=R,minor_radius=r,major_segments=160,minor_segments=48,rotation=rot); return add(o,m)
def rbox(loc,size,m,bevel=0.08,rot=(0,0,0)):
    o=prim(bpy.ops.mesh.primitive_cube_add,location=loc,rotation=rot); o.scale=Vector(size)/2; bpy.ops.object.transform_apply(scale=True)
    md=o.modifiers.new("b","BEVEL"); md.width=bevel; md.segments=12; md.limit_method='NONE'; return add(o,m,shadow_caustic=True)
def bezier_tube(pts,r,m):
    cu=bpy.data.curves.new("c",'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=8; cu.resolution_u=24
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for i,p in enumerate(pts): bp=sp.bezier_points[i]; bp.co=p; bp.handle_left_type=bp.handle_right_type='AUTO'
    o=bpy.data.objects.new("tube",cu); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

# floor + backdrop
fl=prim(bpy.ops.mesh.primitive_plane_add,size=80,location=(0,0,0)); add(fl,floor_mat(),smooth=False); fl.cycles.is_caustics_receiver=True
# lights: key (soft area), rims in brand colors, kicker
def area(loc,look,col,power,size,shape='RECTANGLE',sy=None):
    l=bpy.data.lights.new("a",'AREA'); l.energy=power; l.color=col[:3]; l.shape=shape; l.size=size; l.size_y=sy or size; l.cycles.is_caustics_light=True
    o=bpy.data.objects.new("al",l); bpy.context.collection.objects.link(o); o.location=loc
    d=(Vector(look)-Vector(loc)); o.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); o.visible_glossy=False; o.visible_camera=False; return o
area((-2.5,-4.5,7.5),(0,0,1.2),(1,1,1),900,3.5,sy=2.2)           # key, мягкий сверху-слева
area((-6.5,2.5,3.2),(0,0,1.5),CYAN,900,1.2,sy=4)                 # голубой контровой
area((6.5,2.0,3.0),(0,0,1.5),MAG,900,1.2,sy=4)                   # пурпурный контровой
area((0,7,2.5),(0,0,1.5),(0.7,0.85,1),350,6,sy=1.2)              # задний кикер по кромкам

bd=prim(bpy.ops.mesh.primitive_plane_add,size=1,location=(0,22,7),rotation=(math.radians(90),0,0)); bd.scale=(60,22,1)
m,b,t=mat("backdrop"); n=t.nodes; tc=n.new("ShaderNodeTexCoord")
b.inputs["Base Color"].default_value=(0,0,0,1); b.inputs["Roughness"].default_value=1; b.inputs["Specular IOR Level"].default_value=0
def glow(cx,cy,sx,sy,col,k):
    mp=n.new("ShaderNodeMapping"); mp.inputs["Location"].default_value=(-cx*sx,-cy*sy,0); mp.inputs["Scale"].default_value=(sx,sy,1)
    g=n.new("ShaderNodeTexGradient"); g.gradient_type='SPHERICAL'; t.links.new(tc.outputs["Generated"],mp.inputs["Vector"]); t.links.new(mp.outputs["Vector"],g.inputs["Vector"])
    pw=n.new("ShaderNodeMath"); pw.operation='POWER'; pw.inputs[1].default_value=1.8; t.links.new(g.outputs["Fac"],pw.inputs[0])
    mix=n.new("ShaderNodeMixRGB"); mix.blend_type='MULTIPLY'; mix.inputs["Fac"].default_value=1; mix.inputs["Color1"].default_value=tuple(c*k for c in col[:3])+(1,)
    t.links.new(pw.outputs[0],mix.inputs["Color2"]); return mix
g1=glow(0.40,0.62,1.5,2.0,CY,1.3); g2=glow(0.62,0.30,1.5,2.0,MG,1.3)
ad=n.new("ShaderNodeMixRGB"); ad.blend_type='ADD'; ad.inputs["Fac"].default_value=1; t.links.new(g1.outputs[0],ad.inputs[1]); t.links.new(g2.outputs[0],ad.inputs[2])
base=n.new("ShaderNodeMixRGB"); base.blend_type='ADD'; base.inputs["Fac"].default_value=1; base.inputs["Color1"].default_value=(0.004,0.006,0.012,1); t.links.new(ad.outputs[0],base.inputs[2])
t.links.new(base.outputs[0],b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value=1.0
add(bd,m,smooth=False); bd.visible_shadow=False
cam=bpy.data.cameras.new("cam"); cam.lens=50; cam.sensor_width=36; cam.dof.use_dof=True; cam.dof.aperture_fstop=2.2
co=bpy.data.objects.new("cam",cam); bpy.context.collection.objects.link(co); sc.camera=co
co.location=(0,-16.5,4.4); co.rotation_euler=(math.radians(78),0,0)
cam.dof.focus_distance=16.7; cam.lens=50

random.seed(7)
if MOTIF=="funnel":
    # стеклянная воронка — тело вращения
    prof=[(0.14+1.85*(t/40)**1.35, 0.55+(t/40)*2.6) for t in range(41)]
    me=bpy.data.meshes.new("f"); verts=[];faces=[];N=160
    for j,(r,z) in enumerate(prof):
        for i in range(N): a=2*math.pi*i/N; verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(prof)-1):
        for i in range(N): a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
    me.from_pydata(verts,[],faces); o=bpy.data.objects.new("funnel",me); bpy.context.collection.objects.link(o)
    sol=o.modifiers.new("s","SOLIDIFY"); sol.thickness=0.06; o.modifiers.new("sub","SUBSURF").levels=1
    add(o,glass((0.78,0.93,1.0)),shadow_caustic=True)
    torus((0,0,3.15),1.98,0.05,chrome()); cyl((0,0,0.1),1.0,0.2,chrome())
    sphere((0,0,0.55),0.27,neon(MG,14))
    for i in range(26):
        a=i*2.4; rr=0.3+random.random()*1.35; h=2.3+random.random()*1.1
        m=[chrome(),neon(CY,10),neon(MG,10),glass((1,1,1))][i%4]; sphere((math.cos(a)*rr,math.sin(a)*rr*0.6,h),0.06+random.random()*0.09,m,seg=48)
elif MOTIF=="agents":
    core=prim(bpy.ops.mesh.primitive_ico_sphere_add,location=(0,0,1.7),radius=1.15,subdivisions=1); add(core,glass((0.9,0.85,1.0)),smooth=False,shadow_caustic=True)
    core.rotation_euler=(0.3,0.5,0); sphere((0,0,1.7),0.5,neon(MG,16))
    for p in ((-2.9,-0.6,2.6),(2.9,-0.8,2.8),(-2.4,1.0,0.55),(2.5,1.1,0.6),(0,-1.4,3.6)):
        sphere(p,0.38,chrome()); mid=(Vector((0,0,1.7))+Vector(p))*0.5+Vector((0,0,0.35)); bezier_tube([Vector((0,0,1.7)),mid,Vector(p)],0.025,neon(CY,12))
elif MOTIF=="channel":
    for i,(px,pz,py,w) in enumerate(((-0.6,2.9,-0.4,3.4),(0.4,1.75,0.2,3.0),(-0.2,0.62,0.8,2.6))):
        m=[glass((0.75,0.9,1.0)),chrome(),glass((0.95,0.8,1.0))][i]; b=rbox((px,py,pz),(w,0.42,0.85),m,bevel=0.2,rot=(0,0,-0.25+i*0.12))
        for k in range(2): rbox((px-w*(0.22 if k else 0.1),py-0.23,pz+0.15-k*0.28),(w*(0.45 if k else 0.7),0.05,0.09),neon([CY,MG][k],12),bevel=0.02,rot=(0,0,-0.25+i*0.12))
    st=prim(bpy.ops.mesh.primitive_cone_add,location=(2.3,0.6,2.9),radius1=0.45,depth=0.9,vertices=4); st.scale=(1,0.4,1.5); add(st,neon(CY,14),smooth=False)
elif MOTIF=="seo":
    RC=(-0.6,0,2.35); R=1.35
    torus(RC,R,0.16,chrome(),rot=(math.radians(90),0,0))
    cyl(RC,R-0.08,0.07,glass((0.6,0.85,1.0)),rot=(math.radians(90),0,0))
    ex,ez=RC[0]+R*0.707,RC[2]-R*0.707
    cyl((ex+0.95*0.707,0,ez-0.95*0.707),0.15,2.0,chrome(),rot=(0,math.radians(-45),0))
    sphere((ex+1.9*0.707,0,ez-1.9*0.707),0.18,chrome())
    for i,v in enumerate((0.5,0.9,0.7,1.35,1.1,1.8)):
        m=neon(MG,8) if i==5 else glass((0.7,0.9,1.0) if i%2==0 else (0.95,0.75,1.0)); rbox((-4.2+i*0.42,-0.4,v/2),(0.32,0.32,v),m,bevel=0.06)
elif MOTIF=="si":
    def text(t,loc,m,rot=(math.radians(90),0,0)):
        bpy.ops.object.text_add(location=loc,rotation=rot); o=bpy.context.object; o.data.body=t; o.data.size=1.7; o.data.extrude=0.25; o.data.bevel_depth=0.04; o.data.bevel_resolution=6
        o.data.align_x='CENTER'; o.data.materials.append(m); return o
    text("AI",(-1.75,0,0.55),chrome()); text("SI",(1.85,0,0.55),neon(CY,9))
    cyl((-1.75,-0.55,1.3),0.06,2.9,neon(MG,16),rot=(0,-1.05,0))
    ar=prim(bpy.ops.mesh.primitive_cone_add,location=(0.05,0,1.25),radius1=0.22,depth=0.5,rotation=(0,math.radians(90),0)); add(ar,chrome())

# compositor: glare bloom + slight dispersion + vignette
sc.use_nodes=True; ct=sc.node_tree; ct.nodes.clear(); rl=ct.nodes.new("CompositorNodeRLayers"); gl=ct.nodes.new("CompositorNodeGlare"); gl.glare_type='FOG_GLOW'; gl.threshold=1.4; gl.size=8; gl.mix=-0.35
ld=ct.nodes.new("CompositorNodeLensdist"); ld.inputs["Dispersion"].default_value=0.012; ld.use_fit=True
# vignette via ellipse mask
ell=ct.nodes.new("CompositorNodeEllipseMask"); ell.width=1.35; ell.height=1.25; bl=ct.nodes.new("CompositorNodeBlur"); bl.size_x=bl.size_y=260; bl.filter_type='FAST_GAUSS'; bl.use_relative=False
mr=ct.nodes.new("CompositorNodeMapRange"); mr.inputs[3].default_value=0.35; mr.inputs[4].default_value=1.0
mx=ct.nodes.new("CompositorNodeMixRGB"); mx.blend_type='MULTIPLY'; comp=ct.nodes.new("CompositorNodeComposite")
L=ct.links; L.new(rl.outputs["Image"],gl.inputs["Image"]); L.new(gl.outputs["Image"],ld.inputs["Image"]); L.new(ld.outputs["Image"],mx.inputs[1])
L.new(ell.outputs["Mask"],bl.inputs["Image"]); L.new(bl.outputs["Image"],mr.inputs[0]); L.new(mr.outputs[0],mx.inputs[2]); L.new(mx.outputs["Image"],comp.inputs["Image"])
sc.render.filepath=OUT; bpy.ops.render.render(write_still=True); print("DONE",OUT)
