-- Maneja PCSX-Redux sin intervención: entradas programadas, capturas y save states.
-- Variables de entorno:
--   INPUTS      "frame:BOTON[:duración];..."   INPUTS_FILE  archivo grabado con redux_record.lua
--     ej "2000:START;2600:CROSS:4"  (duración en frames, default 6)
--   SHOT_EVERY  capturar cada N frames (0 = no)       SHOT_FRAMES "f1,f2,..." capturas puntuales
--   SHOT_DIR    carpeta de capturas                    LAST       frame final (cierra el emulador)
--   LOAD_STATE  save state a cargar al inicio          SAVE_STATE ruta donde guardar el estado al llegar a LAST
local env = os.getenv
-- stdout de PCSX-Redux descarta salida cuando se llena su buffer: todo el log va a LOG_FILE
local logf = io.open(env('LOG_FILE') or ((env('SHOT_DIR') or '.') .. '/drive.log'), 'w')
CUR_FRAME = 0
function LOG(s) logf:write(string.format('[f%05d] ', CUR_FRAME), s, '\n'); logf:flush() end
local outdir = env('SHOT_DIR') or '.'
local every = tonumber(env('SHOT_EVERY') or '0')
local last = tonumber(env('LAST') or '1800')
local B = PCSX.CONSTS.PAD.BUTTON
local pad = PCSX.SIO0.slots[1].pads[1]

local marks = {}
for f in string.gmatch(env('SHOT_FRAMES') or '', '%d+') do marks[tonumber(f)] = true end

local presses, releases = {}, {}
-- INPUTS_FILE: grabación de redux_record.lua (líneas "frame:BOTON:dur;", '#' = comentario); se suma a INPUTS
local inputs = (env('INPUTS') or '') .. ';'   -- ';' separa INPUTS de la grabación (si no, "8340:CIRCLE2460:…")
if env('INPUTS_FILE') then
  for line in io.lines(env('INPUTS_FILE')) do
    if not string.match(line, '^%s*#') then inputs = inputs .. line end
  end
end
for f, btn, dur in string.gmatch(inputs, '(%d+):(%a[%w]*):?(%d*)') do
  f = tonumber(f); dur = tonumber(dur) or 6
  assert(B[btn], 'botón desconocido: ' .. btn)
  presses[f] = presses[f] or {}; table.insert(presses[f], B[btn])
  releases[f + dur] = releases[f + dur] or {}; table.insert(releases[f + dur], B[btn])
end

local function shot(frame)
  local ss = PCSX.GPU.takeScreenShot()
  local data = tostring(ss.data)
  local bpp = (#data == ss.width * ss.height * 2) and 16 or 24
  local f = io.open(string.format('%s/f%05d_%dx%d_%d.raw', outdir, frame, ss.width, ss.height, bpp), 'wb')
  f:write(data); f:close()
end

-- DUMP_RAM "frame:ruta[;frame:ruta...]"   vuelca los 2 MB de RAM en esos frames
-- BP_READ  "0x80xxxxxx[:ancho]"  breakpoint de lectura: loguea PC/RA/registros en cada acceso (máx BP_MAX)
local ffi = require('ffi')
local dumps = {}
for f, path in string.gmatch(env('DUMP_RAM') or '', '(%d+):([^;]+)') do dumps[tonumber(f)] = path end
local function dump_ram(path)
  local f = io.open(path, 'wb'); f:write(ffi.string(PCSX.getMemPtr(), 0x200000)); f:close()
end
-- POKE "cuadro:0x80xxxxxx:ancho:valor[;...]"  escribe en RAM (ancho 1/2/4) en cada cuadro desde `cuadro`
-- (sirve para forzar situaciones de prueba sin cambiar archivos del disco, que desfasan las grabaciones)
local pokes = {}
for f, a, w, v in string.gmatch(env('POKE') or '', '(%d+):(0x%x+):(%d):(%w+)') do
  pokes[#pokes + 1] = {tonumber(f), bit.band(tonumber(a), 0x1fffff), tonumber(w), tonumber(v)}
end
local function do_pokes(fr)
  local mem = ffi.cast('uint8_t*', PCSX.getMemPtr())
  for _, p in ipairs(pokes) do
    if fr >= p[1] then
      for i = 0, p[3] - 1 do mem[p[2] + i] = bit.band(bit.rshift(p[4], 8 * i), 0xff) end
    end
  end
end
local bp_hits, bp_max = 0, tonumber(env('BP_MAX') or '40')
-- los handles de breakpoints deben quedar referenciados: si el GC de Lua los recoge, el breakpoint desaparece
BP_HANDLES = {}
local function arm_bp()
    -- BP_READ / BP_WRITE admiten varias direcciones separadas por coma ("0xADDR[:ancho],...")
  local specs = {}
  for addr, width in string.gmatch(env('BP_READ') or '', '(0x%x+):?(%d*)') do specs[#specs + 1] = {addr, width, 'Read'} end
  for addr, width in string.gmatch(env('BP_WRITE') or '', '(0x%x+):?(%d*)') do specs[#specs + 1] = {addr, width, 'Write'} end
  -- PCSX-Redux solo respeta anchos de 1/2/4 bytes: los rangos se parten en bloques de 4
  local chunks = {}
  for _, sp in ipairs(specs) do
    local a0, len = tonumber(sp[1]), tonumber(sp[2]) or 1
    for a = a0, a0 + len - 1, 4 do chunks[#chunks + 1] = {a, math.min(4, a0 + len - a), sp[3]} end
  end
  for _, ch in ipairs(chunks) do
  local addr, width, kind = ch[1], ch[2], ch[3]
  BP_HANDLES[#BP_HANDLES + 1] = PCSX.addBreakpoint(addr, kind, width, 'lua', function(address, w, cause)
    local r = PCSX.getRegisters()
    bp_hits = bp_hits + 1
    if bp_hits <= bp_max then
      LOG(string.format('BP ' .. kind .. ' %08x pc=%08x ra=%08x a0=%08x a1=%08x a2=%08x v0=%08x v1=%08x sp=%08x',
        address, r.pc, r.GPR.n.ra, r.GPR.n.a0, r.GPR.n.a1, r.GPR.n.a2, r.GPR.n.v0, r.GPR.n.v1, r.GPR.n.sp))
    end
    return true  -- true = mantener el breakpoint (false lo elimina)
  end)
  end
  -- BP_EXEC "0x80xxxxxx,..."  loguea registros y el string apuntado por BP_STRREG (a0..a3, default a1)
  local mem = ffi.cast('uint8_t*', PCSX.getMemPtr())
  local reg = env('BP_STRREG') or 'a1'
  for addr in string.gmatch(env('BP_EXEC') or '', '(0x%x+)') do
    BP_HANDLES[#BP_HANDLES + 1] = PCSX.addBreakpoint(tonumber(addr), 'Exec', 4, 'lua', function()
      local r = PCSX.getRegisters()
      bp_hits = bp_hits + 1
      if bp_hits <= bp_max then
        local p = bit.band(r.GPR.n[reg], 0x1fffff)
        local s = {}
        for i = 0, 47 do local c = mem[p + i]; if c == 0 then break end; s[#s + 1] = string.format('%02x', c) end
        LOG(string.format('BP exec %08x ra=%08x a0=%08x a1=%08x a2=%08x a3=%08x str=%s',
          r.pc, r.GPR.n.ra, r.GPR.n.a0, r.GPR.n.a1, r.GPR.n.a2, r.GPR.n.a3, table.concat(s)))
      end
      return true  -- mantener
    end)
  end
end

local loaded = false
local frame = 0
listener = PCSX.Events.createEventListener('GPU::Vsync', function()
  if not loaded and env('LOAD_STATE') then
    loaded = true
    local file = Support.File.open(env('LOAD_STATE'))
    PCSX.loadSaveState(file); file:close()
    return
  end
  frame = frame + 1
  CUR_FRAME = frame
  if frame == tonumber(env('BP_FROM') or '1') then arm_bp() end
  if dumps[frame] then dump_ram(dumps[frame]) end
  if #pokes > 0 then do_pokes(frame) end
  for _, b in ipairs(presses[frame] or {}) do pad.setOverride(b) end
  for _, b in ipairs(releases[frame] or {}) do pad.clearOverride(b) end
  if marks[frame] or (every > 0 and frame % every == 0) then shot(frame) end
  if frame >= last then
    if env('SAVE_STATE') then
      local f = io.open(env('SAVE_STATE'), 'wb'); f:write(tostring(PCSX.createSaveState())); f:close()
    end
    PCSX.quit(0)
  end
end)

-- Módulos opcionales: COVER_FILE activa la cobertura por función (redux_cover.lua, misma carpeta)
if env('COVER_FILE') then
  dofile(env('COVER_SCRIPT') or (string.match(debug.getinfo(1, 'S').source, '^@(.*/)') .. 'redux_cover.lua'))
end
