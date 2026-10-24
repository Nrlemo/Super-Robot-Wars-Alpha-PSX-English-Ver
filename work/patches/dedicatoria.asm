; Pantalla de dedicatoria después del copyright (#279). La arma tools/src/dedicatoria.py (etapa "dedicatoria"):
;   armips dedicatoria.asm -strequ MOVE_IN … -strequ MOVE_OUT … -strequ TITL_FILE … -strequ DATA …
; Reusa la máquina de estados del copyright (TITL FUN_801045f4, estado 0x80112D48, contador 0x80112D49) y su tabla
; de 12 sprites: al terminar el copyright reescribe los campos de los 36 registros (3 secuencias) con los de la
; dedicatoria y vuelve al estado 0; al terminar la dedicatoria restaura los del copyright y sigue al video.
; El código vive en la cola del último sector de OVL/MOVE_GRP.BIN (carga en 0x8011308C; cola 0x80114AC4–0x8011508C,
; 1.480 B): el juego ya la carga y la RAM de ahí no se usa durante el título. Ver notes/graficos.md.
; Solo usa t0–t9 (los llamadores no los esperan intactos) y no toca la pila.
.psx

COUNTER equ 0x80112D49          ; contador de cuadros del estado 2 (byte; el copyright espera 0xB4)

.open MOVE_IN, MOVE_OUT, 0x8011308C
.org 0x80114AC4
.area 0x8011508C - 0x80114AC4

ded_phase:  .byte 0             ; 0 = copyright, 1 = dedicatoria, 2 = terminado (el copyright repetido va al video)
ded_tick:   .byte 0
.align 4

; Estado 4 del copyright terminado (reemplaza `jal 0x80104888` en 0x801047E4; estado y contador ya están en 0).
ded_next:
    lui     t0, hi(ded_phase)
    lbu     t1, lo(ded_phase)(t0)
    move    t9, ra
    bnez    t1, @@video
    li      t2, 1
    sb      t2, lo(ded_phase)(t0)           ; 1.ª vez: pasar a la dedicatoria
    sb      zero, lo(ded_tick)(t0)
    la      t3, ded_recs
    jal     ded_copy
    nop
    j       0x80104814                      ; dibuja el fondo de estrellas y devuelve 0 (sin pasar al video)
    nop
@@video:
    li      t2, 2
    sb      t2, lo(ded_phase)(t0)
    la      t3, cop_recs                    ; dejar la tabla como la espera el copyright
    jal     ded_copy
    nop
    j       0x80104888                      ; lo original: preparar el video (vuelve a 0x801047EC)
    move    ra, t9

; Estado 2 (reemplaza `jal 0x80106328` en 0x80104700): con la dedicatoria el contador avanza un cuadro de cada dos
; (0xB4 → el doble de tiempo). a0–a2 siguen siendo los argumentos de 0x80106328.
ded_hold:
    lui     t0, hi(ded_phase)
    lbu     t1, lo(ded_phase)(t0)
    li      t2, 1
    bne     t1, t2, @@draw
    lbu     t1, lo(ded_tick)(t0)
    nop
    xori    t1, t1, 1
    beqz    t1, @@draw
    sb      t1, lo(ded_tick)(t0)
    lui     t3, hi(COUNTER)
    lbu     t2, lo(COUNTER)(t3)
    nop
    addiu   t2, t2, -1                      ; el llamador suma 1 después: este cuadro no cuenta
    sb      t2, lo(COUNTER)(t3)
@@draw:
    j       0x80106328
    nop

; Copia 12 × 6 halfwords (t3) a los campos +4, +8, +10, +16, +28, +30 de los registros de las 3 secuencias.
ded_copy:
    la      t4, ded_tabs
    li      t7, 3
@@tab:
    lw      t6, 0(t4)
    move    t5, t3
    li      t8, 12
@@rec:
    lhu     t0, 0(t5)
    lhu     t1, 2(t5)
    lhu     t2, 4(t5)
    sh      t0, 4(t6)
    sh      t1, 8(t6)
    sh      t2, 10(t6)
    lhu     t0, 6(t5)
    lhu     t1, 8(t5)
    lhu     t2, 10(t5)
    sh      t0, 16(t6)
    sh      t1, 28(t6)
    sh      t2, 30(t6)
    addiu   t5, t5, 12
    addiu   t8, t8, -1
    bnez    t8, @@rec
    addiu   t6, t6, 32
    addiu   t7, t7, -1
    bnez    t7, @@tab
    addiu   t4, t4, 4
    jr      ra
    lui     t0, hi(ded_phase)               ; ded_next sigue usando t0

.include DATA                               ; REC0–REC2, ded_recs, cop_recs
.align 4
ded_tabs:   .word REC0, REC1, REC2

.endarea
.close

.open TITL_FILE, 0x800FF190
.org 0x80104700
    jal     ded_hold
.org 0x801047E4
    jal     ded_next
.close
