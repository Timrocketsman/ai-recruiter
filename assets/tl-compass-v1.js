/* TimLabs compass. A single small WebGL scene, scheduled by the site's TL.tick. */
(() => {
  const canvas = document.querySelector(".tl-compass-canvas");
  if (!canvas || !window.TL) return;
  const stage = canvas.parentElement;
  let gl;
  try {
    gl = canvas.getContext("webgl", {
      alpha: true, antialias: true, failIfMajorPerformanceCaveat: !stage.hasAttribute("data-render-poster")
    });
    if (!gl) return;
    const program = gl.createProgram();
    function shader(kind, source) {
      const compiled = gl.createShader(kind);
      gl.shaderSource(compiled, source);
      gl.compileShader(compiled);
      if (!gl.getShaderParameter(compiled, gl.COMPILE_STATUS)) throw Error("compass shader");
      gl.attachShader(program, compiled);
      gl.deleteShader(compiled);
    }
    shader(gl.VERTEX_SHADER, `
      attribute vec3 p, n;
      attribute float tone;
      uniform vec2 turn;
      uniform float aspect, open;
      varying vec3 normal, pos;
      varying float material;
      vec3 rotate(vec3 v) {
        float c = cos(turn.x), s = sin(turn.x);
        v = vec3(c*v.x+s*v.z,v.y,-s*v.x+c*v.z);
        c = cos(turn.y); s = sin(turn.y);
        return vec3(v.x,c*v.y-s*v.z,s*v.y+c*v.z);
      }
      void main() {
        pos = rotate(p + vec3(0.,0.,(tone-.8)*open));
        normal = rotate(n);
        material = tone;
        float w = 5.5 - pos.z;
        gl_Position = vec4(pos.x * min(4.1/aspect,4.1),pos.y * min(4.1,4.1*aspect),w*.92-.6,w);
      }
    `);
    shader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec3 normal, pos;
      varying float material;
      uniform float light, phase;
      void main() {
        vec3 N = normalize(normal);
        vec3 V = normalize(vec3(0.,0.,5.5)-pos);
        vec3 A = normalize(vec3(-.6,.75,.65));
        vec3 B = normalize(vec3(.75+phase*.35,-.22,.45));
        float key = max(0.,dot(N,A));
        float fill = max(0.,dot(N,B));
        float spec = pow(max(0.,dot(N,normalize(A+V))),22.);
        float edge = pow(1.-max(0.,dot(N,V)),2.);
        vec3 metal = mix(vec3(.035,.06,.106),vec3(.28,.35,.45),light);
        vec3 color = metal*(.55+key*1.38) + vec3(.15,.36,.56)*fill
                   + vec3(.54,.69,.86)*spec*.72 + vec3(.25,.24,.45)*edge*.55;
        if (material > 2.) color = mix(vec3(.27,.67,.86),vec3(.53,.40,.84),clamp(pos.x*.4+.48,0.,1.)) * (.74+key*.50);
        else if (material > .8) color += vec3(.10,.14,.24)*(.3+key*.6);
        if (material > 3.) color = vec3(.79,.88,.96)*(.7+key*.30);
        gl_FragColor = vec4(color,1.);
      }
    `);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error("compass program");
    gl.useProgram(program);
    const vertices = [];
    function quad(a, b, c, d, material) {
      const u = b.map((v, i) => v - a[i]);
      const v = c.map((x, i) => x - a[i]);
      const normal = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
      const length = Math.hypot(...normal) || 1;
      const n = normal.map(x => -x / length);
      for (const p of [a,b,c,a,c,d]) vertices.push(...p, ...n, material);
    }
    function arc({radius, width, depth, begin, span, z, bend, material, facets = 96}) {
      function profile(i) {
        const t = begin + span * i / facets;
        const wave = z + bend * Math.sin(t + .3);
        return [[radius-width,0],[radius,0],[radius,depth],[radius-width,depth]].map(([r, d]) =>
          [r*Math.cos(t),r*Math.sin(t),wave+d]);
      }
      let previous = profile(0);
      quad(previous[3],previous[2],previous[1],previous[0],material);
      for (let i = 1; i <= facets; i++) {
        const next = profile(i);
        for (let side = 0; side < 4; side++) {
          const j = (side + 1) % 4;
          quad(previous[side],previous[j],next[j],next[side],material);
        }
        previous = next;
      }
      quad(previous[0],previous[1],previous[2],previous[3],material);
    }
    arc({radius:1.32,width:.22,depth:.22,begin:.53,span:4.43,z:-.34,bend:.27,material:.2});
    arc({radius:1.12,width:.035,depth:.017,begin:.57,span:4.26,z:-.105,bend:.27,material:2.5});
    arc({radius:1.03,width:.22,depth:.18,begin:3.87,span:4.43,z:-.04,bend:-.30,material:.88});
    arc({radius:1.038,width:.023,depth:.016,begin:4.01,span:4.17,z:.15,bend:-.30,material:2.15});
    arc({radius:.70,width:.195,depth:.16,begin:.58,span:4.53,z:.24,bend:.22,material:1.15});
    arc({radius:.51,width:.020,depth:.010,begin:.64,span:4.37,z:.41,bend:.22,material:2.15});
    arc({radius:.260,width:.255,depth:.14,begin:0,span:Math.PI*2,z:.17,bend:0,material:1.2,facets:6});
    arc({radius:.105,width:.104,depth:.015,begin:0,span:Math.PI*2,z:.312,bend:0,material:3.1,facets:6});
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);
    for (const [name, size, offset] of [["p",3,0],["n",3,12],["tone",1,24]]) {
      const attribute = gl.getAttribLocation(program,name);
      gl.enableVertexAttribArray(attribute);
      gl.vertexAttribPointer(attribute,size,gl.FLOAT,false,28,offset);
    }
    const uniform = Object.fromEntries(["turn","aspect","open","light","phase"].map(name => [name,gl.getUniformLocation(program,name)]));
    gl.enable(gl.DEPTH_TEST);
    gl.clearColor(0,0,0,0);
    let width = 0, height = 0, x = 0, y = 0, aimX = 0, aimY = 0;
    let opened = 0, start = null, last = -Infinity, inView = true, lost = false, invalidated = true;
    const still = stage.hasAttribute("data-render-poster");
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const light = matchMedia("(prefers-color-scheme: light)");
    const page = document.documentElement;
    const isLight = () => page.dataset.theme === "light" || (!page.dataset.theme && light.matches);
    function render(time = 0) {
      if (lost || !inView || document.hidden || time-last < 30 && !invalidated) return;
      const paused = stage.closest(".tl-home-hero")?.classList.contains("tl-paused") || motion.matches || still;
      if (paused && !invalidated) { TL.tick.remove(render); return; }
      last = time;
      if (start === null) start = time;
      const elapsed = paused ? 1 : Math.min(1,(time-start)/950);
      const rise = 1 - (1-elapsed)**3;
      x += ((paused ? 0 : aimX)-x)*.16;
      y += ((paused ? 0 : aimY)-y)*.16;
      opened += ((paused ? 0 : Math.min(1,Math.max(0,-stage.getBoundingClientRect().top/stage.clientHeight)))-opened)*.13;
      const size = stage.getBoundingClientRect();
      const scale = Math.min(devicePixelRatio, 1.25, 750/Math.max(size.width,size.height));
      const w = Math.max(1,Math.round(size.width*scale));
      const h = Math.max(1,Math.round(size.height*scale));
      if (w !== width || h !== height) {
        width = canvas.width = w; height = canvas.height = h;
        gl.viewport(0,0,w,h);
      }
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      const phase = paused ? 0 : Math.sin(time/4800);
      gl.uniform2f(uniform.turn,-.38 + x*.14 + (1-rise)*.42 + phase*.038,.36 + y*.14);
      gl.uniform1f(uniform.open,(1-rise)*.16 + opened*.09);
      gl.uniform1f(uniform.aspect,w/h);
      gl.uniform1f(uniform.light,isLight() ? 1 : 0);
      gl.uniform1f(uniform.phase,phase);
      gl.drawArrays(gl.TRIANGLES,0,vertices.length/7);
      invalidated = false;
      stage.classList.add("tl-rendered");
      if (paused) TL.tick.remove(render);
    }
    const wake = () => {
      invalidated = true;
      if (!lost && inView && !document.hidden) TL.tick.add(render);
    };
    canvas.addEventListener("webglcontextlost", event => {
      event.preventDefault();
      lost = true;
      TL.tick.remove(render);
      stage.classList.remove("tl-rendered");
    });
    stage.addEventListener("pointermove", event => {
      const rect = stage.getBoundingClientRect();
      aimX = (event.clientX-rect.left)/rect.width*2-1;
      aimY = (event.clientY-rect.top)/rect.height*2-1;
    },{passive:true});
    stage.addEventListener("pointerleave", () => { aimX = 0; aimY = 0; });
    stage.addEventListener("tl-motion-state",wake);
    motion.addEventListener("change",wake);
    light.addEventListener("change",wake);
    new MutationObserver(wake).observe(page,{attributes:true,attributeFilter:["data-theme"]});
    new ResizeObserver(wake).observe(stage);
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      if (inView) wake(); else TL.tick.remove(render);
    }).observe(stage);
    if (still) { render(); gl.finish(); } else wake();
  } catch {
    stage.classList.remove("tl-rendered");
  }
})();
