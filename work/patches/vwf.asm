; VWF (ancho variable) para texto de 1 byte en el maquetador de texto FUN_80018cc4 (SLPS_026.36).
; Reescribe 0x80018F30-0x80018F74 (18 instrucciones, mismo tamaño):
;  - conserva el manejo de ﾞ (0xDE, +0x30 al glifo) y ﾟ (0xDF, +0x40) con avance 8
;  - para el resto: avance = VWF_TABLE[carácter] en vez de 8 fijo
; a3 se usa como temporal: el original lo pone en 0 en 0x80018F7C, justo después.
; Ver work/notes/vwf_investigacion.md
.psx
.open "iso_jp/SLPS_026.36", "build/exe/SLPS_026.36", 0x80010000 - 0x800

VWF_TABLE equ 0x80059480        ; 256 bytes en zona de ceros sin uso aparente (0x80059404-0x80059606)

.org 0x80018F30
    lbu     v1, 0x0(s0)         ; siguiente byte (¿ﾞ/ﾟ?)
    li      v0, 0xDE
    beq     v1, v0, @@mark
    li      a3, 0x30
    li      v0, 0xDF
    beq     v1, v0, @@mark
    li      a3, 0x40
    lbu     a1, -0x1(s0)        ; carácter actual (s0 ya avanzó)
    lui     v0, hi(VWF_TABLE)
    addu    v0, v0, a1
    j       0x80018F78
    lbu     a1, lo(VWF_TABLE)(v0)
@@mark:
    lbu     v0, 0xD(s1)
    addiu   s0, s0, 0x1
    addu    v0, v0, a3
    sb      v0, 0xD(s1)
    j       0x80018F78
    li      a1, 0x8
.if . != 0x80018F78
    .error "el bloque VWF no ocupa exactamente 0x80018F30-0x80018F74"
.endif

.org VWF_TABLE
    .incbin "patches/vwf_table.bin"

; Tabla de objetos de texto (#57): el juego reserva al arrancar 0x300 objetos de 0x1C bytes (uno por carácter en
; pantalla, FUN_80018578 vía FUN_80018B28). En inglés cada letra es un objeto y la pantalla de ingreso del
; protagonista pasaba de 768: el asignador devolvía -1 y se perdían el título, el menú y los valores.
; Ver work/notes/menus.md ("Tope de objetos de texto").
TEXT_OBJS equ 0x500
.org 0x80014AC8
    li      a1, TEXT_OBJS       ; original: addiu a1, zero, 0x300

.close
