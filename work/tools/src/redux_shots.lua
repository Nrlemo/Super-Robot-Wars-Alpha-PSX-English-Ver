-- Captura screenshots en frames fijos y cierra el emulador (smoke test de boot)
local outdir = os.getenv('SHOT_DIR') or '.'
local marks = {}
for f in string.gmatch(os.getenv('SHOT_FRAMES') or '600,1200,1800', '%d+') do marks[tonumber(f)] = true end
local last = tonumber(os.getenv('SHOT_LAST') or '1800')
local frame = 0
listener = PCSX.Events.createEventListener('GPU::Vsync', function()
  frame = frame + 1
  if marks[frame] then
    local ss = PCSX.GPU.takeScreenShot()
    local data = tostring(ss.data)
    local bpp = (#data == ss.width * ss.height * 2) and 16 or 24
    local f = io.open(string.format('%s/f%05d_%dx%d_%d.raw', outdir, frame, ss.width, ss.height, bpp), 'wb')
    f:write(data); f:close()
    print('shot', frame, ss.width, ss.height, bpp)
  end
  if frame >= last then PCSX.quit(0) end
end)
