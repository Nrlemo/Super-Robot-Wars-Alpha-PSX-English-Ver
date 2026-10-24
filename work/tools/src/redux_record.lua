-- Grabador de inputs para PCSX-Redux: guarda qué botones se tocan y en qué cuadro, en el mismo formato
-- INPUTS="frame:BOTON:duración;..." que reproduce redux_drive.lua (drive.sh) en server1.
--
-- El cuadro se cuenta igual que en redux_drive.lua (un tick por GPU::Vsync desde que se carga el script),
-- así que el script tiene que cargarse al arrancar con -dofile (ver saves/grabar.sh), NO después desde la consola.
--
-- Salida: <proyecto>/saves/grabaciones/rec_AAAAMMDD_HHMMSS.txt (o REC_FILE). Una entrada por línea, se escribe
-- al soltar cada botón (si el emulador se cierra de golpe, se pierde a lo sumo lo que estaba apretado).
local B = PCSX.CONSTS.PAD.BUTTON
local pad = PCSX.SIO0.slots[1].pads[1]
local NAMES = { 'SELECT', 'START',  -- L3/R3 no existen en PCSX.CONSTS.PAD.BUTTON (pad digital)
                'UP', 'RIGHT', 'DOWN', 'LEFT',
                'L2', 'R2', 'L1', 'R1', 'TRIANGLE', 'CIRCLE', 'CROSS', 'SQUARE' }

-- carpeta del proyecto: este archivo vive en <proyecto>/work/tools/src/
local here = string.match(debug.getinfo(1, 'S').source, '^@(.*/)') or './'
local root = here .. '../../../'
local path = os.getenv('REC_FILE') or (root .. 'saves/grabaciones/rec_' .. os.date('%Y%m%d_%H%M%S') .. '.txt')
os.execute('mkdir -p "' .. string.match(path, '^(.*)/') .. '"')
local out = assert(io.open(path, 'w'))
out:write('# Grabación de inputs SRW Alpha — ', os.date('%Y-%m-%d %H:%M:%S'), '\n')
out:write('# ISO: ', os.getenv('REC_ISO') or '(no indicada)', '\n')
out:write('# card inicial: ', os.getenv('REC_CARD') or '(no indicada)', '\n')
out:write('# formato frame:BOTON:duración; (reproducir en server1 con drive.sh ... INPUTS_FILE=<este archivo>)\n')
out:flush()
print('[rec] grabando en ' .. path)

local frame, down, n = 0, {}, 0
REC_LISTENER = PCSX.Events.createEventListener('GPU::Vsync', function()  -- global: si el GC lo recoge, deja de grabar
  frame = frame + 1
  for _, name in ipairs(NAMES) do
    local pressed = pad.getButton(B[name])
    if pressed and not down[name] then
      down[name] = frame
    elseif not pressed and down[name] then
      local start = down[name]
      down[name] = nil
      out:write(string.format('%d:%s:%d;\n', start, name, frame - start))
      out:flush()
      n = n + 1
      print(string.format('[rec] f%05d %s (%d cuadros)', start, name, frame - start))
    end
  end
  if frame % 600 == 0 then  -- marca de tiempo cada 10 s para ubicarse al revisar la grabación
    out:write(string.format('# f%05d (%d entradas)\n', frame, n)); out:flush()
  end
end)
