-- Cobertura por función: breakpoint de ejecución en cada entrada listada en COVER_FILE ("0xADDR nombre" por línea).
-- Se arma en el frame COVER_FROM y, al llegar a LAST, imprime "COV addr primer_frame llamadas nombre".
-- Complementa a redux_drive.lua (cargar primero ese script: comparte LOAD_STATE, INPUTS y LAST).
local env = os.getenv
local from = tonumber(env('COVER_FROM') or '1')
local last = tonumber(env('LAST') or '1800')
local funcs = {}
for line in io.lines(env('COVER_FILE')) do
  local a, name = string.match(line, '(0x%x+)%s+(%S+)')
  if a then funcs[#funcs + 1] = {tonumber(a), name} end
end
local first, count, frame, armed = {}, {}, 0, false
COVER_HANDLES = {}  -- mantener referencias (el GC eliminaría los breakpoints)
-- global: si fuera local, el GC de Lua eliminaría el listener al terminar el dofile
COVER_LISTENER = PCSX.Events.createEventListener('GPU::Vsync', function()
  frame = frame + 1
  if frame == from and not armed then
    armed = true
    for _, f in ipairs(funcs) do
      local addr = f[1]
      local bp
      bp = PCSX.addBreakpoint(addr, 'Exec', 4, 'cover', function()
        count[addr] = (count[addr] or 0) + 1
        if not first[addr] then first[addr] = frame end
        -- el valor devuelto decide si el breakpoint sigue: a las 50 llamadas se elimina (funciones calientes)
        return count[addr] < 50
      end)
      COVER_HANDLES[#COVER_HANDLES + 1] = bp
    end
    LOG('COVER armado: ' .. #funcs .. ' funciones')
  end
  if frame == last - 1 then
    for _, f in ipairs(funcs) do
      if first[f[1]] then LOG(string.format('COV %08x %d %d %s', f[1], first[f[1]], count[f[1]], f[2])) end
    end
  end
end)
