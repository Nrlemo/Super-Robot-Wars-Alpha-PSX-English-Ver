import csv, sys
SRC = 'work/glossary/weapons_en.csv'
OUT = 'work/glossary/weapons_review.csv'
GW = 'Gundam Wiki (gundam.fandom.com)'
# jp: (en, en_short, status, source, rationale)   en_short None = same as en
R = {
# ---- dudosos / proposed ----
'ハイドボンブレイヤー': ('Hide Bomb Dispenser', None, 'resolved', f'{GW} (Zaku III Custom: "hide bomb dispenser"); JP wikis: ハイド・ボンブ投下器(レイヤー)',
  'Maintainer confirmed ハイドボンブ = "Hide Bomb". ハイド・ボンブ = space mine dropped from the left shoulder box; レイヤー = mine-layer. English Gundam sources call it "hide bomb dispenser" (exactly 19 bytes). Alt: "Hide Bomb Layer".'),
'ハンドソルト': ('Hand Sold', None, 'decided', 'maintainer decision 2026-09-27; SRW Wiki JP (ゼン2号): pronounced ハンドソルド in the anime; screw-type hand cutter',
  'Follows the anime pronunciation (ソルド) and avoids the unintended "Hand Salt".'),
'ドスブレッシャー': ('Dos Pressure', None, 'decided', 'maintainer decision 2026-09-27; JP wikis: design name ドスプレッシャー (4-blade rotary wing cutter); Hyoma shouts it in BXCLIST msg 810',
  'Uses the original design-sheet name. NamuWiki-EN "Dos Brasher" rejected.'),
'ギスト・ブロー': ('Gist Blow', None, 'decided', 'maintainer decision 2026-09-27; SRW Wiki JP (ゼカリア): energy-coated manipulator punch',
  'Literal. Must NOT become "Geist Blow": that name already belongs to Ezekiel\'s ガイスト・ブロー.'),
'クローミサイル': ('Claw Missile', None, 'fan-standard', 'literal; Big Zam leg claws', 'Literal and self-explanatory; no competing English name found.'),
'爆導索': ('Demolition Chain Mine', 'Demolition Chain', 'resolved', f'{GW} (GP03 Dendrobium: "Demolition Chain Mines")',
  'Official-style English from Gundam sources replaces the literal "Explosive Cable". Short drops the generic "Mine".'),
'集束ミサイル': ('Cluster Missile', None, 'fan-standard', 'literal (集束 = clustered)', 'Standard military term; fits.'),
'偏向メガ粒子砲': ('Deflection Mega Particle Cannon', 'Deflect Mega Cannon', 'resolved', f'{GW} (Neue Ziel: "Deflection Type Mega Particle Cannon" x9)',
  'Full name confirmed. Short keeps "Deflect" (recognizable) and uses the Mega Cannon convention; replaces "Bent Mega Cannon".'),
'格闘': ('Melee Attack', None, 'fan-standard', 'convention; OG-EN uses "Melee" for the stat', 'Generic unarmed attack; neutral wording works for EVA, beasts, Valkyries.'),
'バグ援護攻撃': ('Bug Support Attack', None, 'fan-standard', 'Gundam F91 (official "Bugs")', '援護攻撃 = support attack (SRW-EN term). Fits in 18 bytes.'),
'八手ビームサーベル': ('8-Way Beam Saber', None, 'fan-standard', 'literal (八手 = eight hands)', 'Multi-direction saber combo; no official English. Keep.'),
'ホイールプレッシャー': ('Wheel Pressure', None, 'fan-standard', 'katakana transliteration', 'Direct loanword; keep.'),
'実弾ライフル': ('Ballistic Rifle', None, 'fan-standard', 'literal (実弾 = live ammunition)', '"Ballistic" is the usual English opposite of beam weapons.'),
'マックライアット': ('Mack Riot', None, 'resolved', 'Getter Robo Wiki / Texas Mack: the two revolvers combine into a shotgun or a rifle',
  'ライアット = riot (gun), i.e. the shotgun form; the rifle form is the separate "Mack Rifle". Keep "Mack Riot".'),
'ナルマグネ光線': ('Null Magne Ray', None, 'resolved', 'game text DC: ナルマグネ光線で強制分離 (forces Combattler V to separate)',
  'ナル = null: the ray cancels the magnetism that holds the Battle Machines together. Replaces the meaningless "Narumagne Ray".'),
'神空剣': ('Shinkuken', None, 'fan-standard', 'romanized; parallels Voltes V 天空剣 "Tenkuken"', 'Romanization mirrors Tenkuken. Alt descriptive: "Divine Sky Sword".'),
'紅玉式光線主砲': ('Ruby Main Beam Cannon', 'Ruby Main Cannon', 'fan-standard', 'literal (紅玉 = ruby)', 'Exelion main gun; short drops "Beam".'),
'兵隊': ('Soldier Swarm', None, 'fan-standard', 'literal (landing craft deploys Space Monster soldiers)', 'Keep.'),
'アームド・アタック': ('ARMD Attack', None, 'resolved', 'Macross official: ARMD carriers', 'Macross punches with the ARMD carrier arm. Keep.'),
'ライトソード': ('Light Sword', None, 'fan-standard', 'literal', 'Keep.'),
'マグマ・ヴァサール': ('Magma Vassal', None, 'official', 'Akurasu OGs Mech Database Others (info/): RyuKoOh "Magma Vassal"', 'OGs name wins over the fan spelling "Magma Vasarl".'),
'R-コンビネーション': ('R-Combination', None, 'fan-standard', 'katakana transliteration', 'Keep.'),
'念動シュート': ('TK Shoot', None, 'fan-standard', 'Super Robot Spirits guide: "Nendo Shoot"; 念動 = TK (glossary)', 'Consistent with "TK Laser Cannon". Alt: "Nendo Shoot".'),
'アルドレーザー': ('Ald Laser', None, 'resolved', 'Super Robot Wars Wiki (Fandom), Zfylud/Zehirut: "Ald Laser"', 'Confirmed.'),
'ジーベン・ゲバウト': ('Sieben Gebaut', None, 'decided', 'maintainer decision 2026-09-27', 'Literal kept (a "Sieben Gebote" reading was considered and rejected).'),
'タキス・ミサイル': ('Takis Missile', None, 'fan-standard', 'katakana transliteration (BXCLIST msg 3296)', 'Keep.'),
'ゴッドゴーガン把ね撃ち': ('God Gorgon Volley', None, 'fan-standard', 'Raideen official "God Gorgon"; 把ね撃ち (= 束ね撃ち) = bundled shot', 'Keep.'),
# ---- OGs pages (Akurasu) ----
'ガウンジェノサイダー': ('Gaun Genocider', None, 'official', 'Akurasu OGs Mech Database R Series (work/glossary/web/ogs_Mech_Database_R_Series.html)', 'Was fan-standard; confirmed OGs name.'),
'T-LINKブーメラン': ('T-Link Boomerang', None, 'official', 'Akurasu OGs Mech Database R Series (work/glossary/web/ogs_Mech_Database_R_Series.html): R-Gun Powered', 'Was fan-standard; confirmed OGs name.'),
'G・リボルヴァー': ('G-Revolver', None, 'official', 'Akurasu OGs Weapon List (work/glossary/web/ogs_Weapon_List.html)', 'OGs spells it with a hyphen.'),
'龍王破山剣': ('Dragoon Blade', None, 'official', 'Akurasu OGs Mech Database Others (info/): RyuKoOh "Dragoon Blade" (by unit; SRW Wiki Fandom also gives Dragoon Blade = RyuOh Hazanken)', 'OG style (maintainer decision 2026-09-27). Pairs with Wrathcleaver.'),
'計都瞬獄剣': ('Torment Blade', None, 'official', 'Akurasu OGs Barrier Piercing Weapon List (info/, JP+EN pair): 計都瞬獄剣 = "Torment Blade"', 'OG style; Grungust Type 2.'),
'計都羅喉剣': ('Eclipse Slash', None, 'official', 'Akurasu OGs Mech Database Super Robot Grungust (info/): Grungust has "Eclipse Slash" and "Calamity Slash" (= 計都羅睺剣・暗剣殺, JP pair)', 'Inferred by unit: the plain 計都羅睺剣 is the Eclipse Slash. The game writes 喉 for 睺.'),
'アイソリッド・レーザー': ('Eye-Solid Laser', None, 'official', 'Akurasu OGs Mech Database (Grungust Type 2, G-Hawk)', 'OGs spelling.'),
'マルチトレースミサイル': ('Multi-Trace Missiles', 'Multi-Trace Missile', 'official', 'Akurasu OGs Barrier Piercing Weapon List (info/, JP+EN pair)', 'OGs uses the plural (20 bytes), so the menu keeps the singular.'),
'リープミサイル': ('Leap Missiles', None, 'official', 'Akurasu OGs Barrier Piercing Weapon List (info/, JP+EN pair): リープ・ミサイル = "Leap Missiles"', 'OGs uses the plural.'),
'フルインパクト・キャノン': ('Full-Impact Cannon', None, 'official', 'Akurasu OGs Mech Database Real Trooper X (Huckebein Gunner)', 'OGs spelling with hyphen.'),
'Gインパクトキャノン': ('G-Impact Cannon', None, 'official', 'Akurasu OGs Mech Database Real Trooper X (Huckebein Mk-II, AM Gunner)', 'OGs spelling with hyphen.'),
'クロスマッシャー': ('Cross Smasher', None, 'official', 'Akurasu OGs Mech Database Others (info/): Valsione / Valsion Custom "Cross Smasher"', 'OGs spelling.'),
# ---- largos ----
'メガ粒子砲': ('Mega Particle Cannon', 'Mega Particle Gun', 'official', 'Gundam-EN', 'Gundam English sources use "mega particle gun" as well; stays distinct from Neue Ziel\'s "Mega Cannon" (メガカノン砲).'),
'対空機銃': ('Anti-Air Machine Gun', 'AA Machine Gun', 'fan-standard', 'convention', 'AA = anti-air (same as AA Pulse Laser).'),
'75ミリ5連装マシンガン': ('75mm Finger Machine Gun', 'Finger Machine Gun', 'official', 'Gundam-EN', 'Keeps the official name; drops the caliber.'),
'対空メガ粒子砲': ('Anti-Air Mega Particle Cannon', 'AA Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'大型メガ粒子砲': ('Large Mega Particle Cannon', 'Large Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'120ミリ機関砲': ('120mm Machine Cannon', '120mm Autocannon', 'fan-standard', 'convention', '機関砲 = autocannon (standard military English).'),
'サブメガ粒子砲': ('Sub Mega Particle Cannon', 'Sub Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'メインメガ粒子砲': ('Main Mega Particle Cannon', 'Main Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'2連装メガ粒子砲': ('Twin Mega Particle Cannon', 'Twin Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'12連装ミサイルランチャー': ('12-Tube Missile Launcher', '12-Tube Missiles', 'fan-standard', 'convention', '"N-Tube Missiles" convention.'),
'大型ビームマシンガン': ('Large Beam Machine Gun', 'Large Beam MG', 'fan-standard', 'convention', 'MG = machine gun (no shorter full wording fits).'),
'8連多弾倉ミサイルランチャー': ('8-Tube Multi-Magazine Missile Launcher', '8-Tube Missiles', 'fan-standard', 'convention', '"N-Tube Missiles" convention; "multi-magazine" lost.'),
'110ミリ機関砲': ('110mm Machine Cannon', '110mm Autocannon', 'fan-standard', 'convention', 'Autocannon convention.'),
'小型ミサイルランチャー': ('Small Missile Launcher', 'Small Missiles', 'fan-standard', 'convention', '"X Missiles" convention for launchers.'),
'大型ミサイルランチャー': ('Large Missile Launcher', 'Large Missiles', 'fan-standard', 'convention', '"X Missiles" convention.'),
'110ミリ速射砲': ('110mm Rapid-Fire Gun', '110mm Rapid Gun', 'fan-standard', 'convention', 'Drops "-Fire".'),
'メガバズーカランチャー': ('Mega Bazooka Launcher', 'Mega Bazooka', 'official', 'Gundam-EN', 'Common official short name.'),
'拡散メガ粒子砲': ('Scatter Mega Particle Cannon', 'Scatter Mega Cannon', 'fan-standard', 'convention', 'Mega Cannon convention.'),
'小型メガビーム砲': ('Small Mega Beam Cannon', 'Small Mega Beam Gun', 'fan-standard', 'convention', 'Cannon→Gun (small weapon anyway).'),
'メガ拡散ビーム砲': ('Mega Scatter Beam Cannon', 'Mega Scatter Beam', 'fan-standard', 'convention', 'Drops the generic noun.'),
'160ミリ機関砲': ('160mm Machine Cannon', '160mm Autocannon', 'fan-standard', 'convention', 'Autocannon convention.'),
'20連装ミサイルランチャー': ('20-Tube Missile Launcher', '20-Tube Missiles', 'fan-standard', 'convention', '"N-Tube Missiles" convention.'),
'ハイパーメガ粒子砲': ('Hyper Mega Particle Cannon', 'Hyper Mega Cannon', 'official', 'Gundam-EN', 'Mega Cannon convention; distinct from "Hyper Mega Launcher".'),
'180ミリ機関砲': ('180mm Machine Cannon', '180mm Autocannon', 'fan-standard', 'convention', 'Autocannon convention.'),
'140ミリ機関砲': ('140mm Machine Cannon', '140mm Autocannon', 'fan-standard', 'convention', 'Autocannon convention.'),
'ハイメガ粒子砲': ('High Mega Particle Cannon', 'High Mega Particle', 'fan-standard', 'convention', '"High Mega Cannon" would collide with ZZ\'s ハイメガキャノン, so the noun is dropped instead.'),
'対空機関砲': ('Anti-Air Machine Cannon', 'AA Autocannon', 'fan-standard', 'convention', 'AA + Autocannon conventions.'),
'マイクロ・ミサイルランチャー': ('Micro Missile Launcher', 'Micro Missiles', 'fan-standard', 'convention', '"X Missiles" convention.'),
'スプレーミサイルランチャー': ('Spray Missile Launcher', 'Spray Missiles', 'official', 'Gundam-EN', '"X Missiles" convention.'),
'有線式メガアーム砲': ('Wired Mega Arm Cannon', 'Wired Mega Arm Gun', 'fan-standard', 'convention', 'Keeps "Mega Arm"; Cannon→Gun.'),
'2連ショルダービームガン': ('Twin Shoulder Beam Gun', 'Shoulder Beam Guns', 'fan-standard', 'convention', 'Plural carries the "twin".'),
'胸部ミサイルランチャー': ('Chest Missile Launcher', 'Chest Missiles', 'fan-standard', 'convention', '"X Missiles" convention.'),
'ヴァリアブルメガランチャー': ('Variable Mega Launcher', 'Var. Mega Launcher', 'fan-standard', 'convention', 'Only the first word abbreviated.'),
'6連マイクロミサイルポッド': ('6-Tube Micro Missile Pod', '6-Tube Micro Pod', 'fan-standard', 'convention', 'N-Tube convention; "Missile" implied by Micro Pod.'),
'ローリングバスターライフル': ('Rolling Buster Rifle', 'Rolling Buster', 'official', 'Gundam-EN', 'The distinctive shout; the generic noun is dropped.'),
'2連装ビームガトリングガン': ('Twin Beam Gatling Gun', 'Twin Beam Gatling', 'official', 'Gundam-EN', 'Drops "Gun".'),
'サザンクロスナイフ': ('Southern Cross Knife', 'Southern Cross', 'official', 'Mazinger-EN', 'The distinctive shout; the generic noun is dropped. Alt: "S. Cross Knife".'),
'大車輪ロケットパンチ': ('Daisharin Rocket Punch', 'Daisharin R. Punch', 'fan-standard', 'Mazinger fandom', 'Rocket Punch abbreviated to keep the iconic "Daisharin".'),
'スペシャルDXボロットパンチ': ('Special DX Borot Punch', 'SP DX Borot Punch', 'fan-standard', 'convention', 'SP = Special; keeps the "DX" vs plain "Special Borot Punch" distinction.'),
'ドリルプレッシャーパンチ': ('Drill Pressure Punch', 'Drill Pressure', 'official', 'Mazinger-EN', 'The distinctive shout; the generic noun is dropped. Alt: "Drill P. Punch".'),
'超破壊光線': ('Super Destruction Ray', 'Super Destruct Ray', 'fan-standard', 'convention', 'Shout-style compression.'),
'ダブルトマホークブーメラン': ('Double Tomahawk Boomerang', 'Dbl Tomahawk Boomer', 'decided', 'maintainer decision 2026-09-27; Getter-EN',
  '"Double Tomahawk" and "Tomahawk Boomerang" are separate weapons, so neither can be the short.'),
'大雪山おろし二段返し': ('Daisetsuzan Oroshi Nidan-gaeshi', 'Daisetsuzan 2-Stage', 'fan-standard', 'Getter fandom', '"Daisetsuzan Oroshi" is a separate weapon, so 2-Stage marks the variant.'),
'超電磁ボールVの字斬り': ('Chodenji Ball V-Slash', 'Chodenji Ball V-Cut', 'fan-standard', 'convention (Chodenji romanized like the other Chodenji attacks)', 'Slash→Cut keeps every element.'),
'分子破壊砲': ('Molecular Destruction Cannon', 'Molecular Destroyer', 'fan-standard', 'convention', 'Shout-style compression.'),
'断空砲フォーメーション': ('Dankuu Cannon Formation', 'Dankuu Cannon Form.', 'fan-standard', 'Dancouga fandom', 'Keeps "Dankuu Cannon" so it is not confused with the Sword/Kouga attacks.'),
'5連ミサイルランチャー': ('5-Tube Missile Launcher', '5-Tube Missiles', 'fan-standard', 'convention', '"N-Tube Missiles" convention.'),
'高収束ビーム速射砲': ('Focused Rapid Beam Cannon', 'Rapid Beam Cannon', 'fan-standard', 'convention', 'Drops "Focused".'),
'マゴロク・E・ソード': ('Magoroku Exterminate Sword', 'Magoroku E-Sword', 'official', 'Evangelion-EN', 'The official name already abbreviates it to "E".'),
'ポジトロンスナイパーライフル': ('Positron Sniper Rifle', 'Positron Sniper', 'official', 'Evangelion-EN', 'Stays distinct from "Positron Rifle".'),
'イナズマ反転キック': ('Inazuma Reverse Kick', 'Inazuma Turn Kick', 'fan-standard', 'convention (反転 = turnaround)', 'Stays distinct from "Inazuma Kick".'),
'ジャコビニ流星アタック': ('Giacobini Meteor Attack', 'Giacobini Meteor', 'fan-standard', 'Gunbuster fandom', 'Drops the generic noun.'),
'ダブルバスターコレダー': ('Double Buster Collider', 'Dbl Buster Collider', 'fan-standard', 'Gunbuster fandom', 'Stays distinct from "Buster Collider".'),
'バスタートマホークブーメラン': ('Buster Tomahawk Boomerang', 'Buster Boomerang', 'fan-standard', 'Gunbuster fandom', '"Buster Tomahawk" is a separate weapon, so keep Boomerang.'),
'全周熱線砲': ('Omni Heat Ray Cannon', 'Omni Heat Ray', 'fan-standard', 'convention', 'Drops the generic noun.'),
'対空パルスレーザー砲': ('AA Pulse Laser Cannon', 'AA Pulse Laser', 'fan-standard', 'convention', 'Drops the generic noun.'),
'対艦ミサイルランチャー': ('Anti-Ship Missile Launcher', 'Anti-Ship Missiles', 'fan-standard', 'convention', '"X Missiles" convention.'),
'小型自己誘導ミサイル': ('Small Homing Missile', 'Mini Homing Missile', 'fan-standard', 'convention', 'Small→Mini.'),
'超高機動マイクロミサイル': ('High-Maneuver Micro Missile', 'HM Micro Missile', 'official', 'Macross-EN (HMMM)', 'HM prefix stays distinct from the generic "Micro Missile".'),
'誘導収束ビーム砲': ('Guided Focus Beam Cannon', 'Guided Beam Cannon', 'fan-standard', 'convention', 'Drops "Focus".'),
'対艦対空ミサイルランチャー': ('Anti-Ship/Air Missile Launcher', 'AS/AA Missiles', 'fan-standard', 'convention', 'AS/AA + "X Missiles" conventions.'),
'超大型荷電粒子ビーム砲': ('Super Heavy Particle Beam Cannon', 'Heavy Particle Beam', 'fan-standard', 'convention', 'Drops the generic noun.'),
'中口径荷電粒子ビーム砲': ('Mid-Caliber Particle Beam Cannon', 'Mid Particle Beam', 'official', 'Macross-EN', 'Parallel to Heavy Particle Beam.'),
'小口径レーザー対人機銃': ('Anti-Personnel Laser Gun', 'Anti-Pers. Laser', 'fan-standard', 'convention', 'The previous short was 20 bytes.'),
'荷電粒子ビーム砲': ('Charged Particle Beam Cannon', 'Particle Beam Gun', 'official', 'Macross-EN', 'The previous short "Particle Beam Cannon" was 20 bytes.'),
'小型レーザーマシン・ピストル': ('Laser Machine Pistol', 'Laser Auto Pistol', 'fan-standard', 'convention', 'Machine pistol = automatic pistol.'),
'龍王破山剣・逆鱗断': ('Wrathcleaver', None, 'official', 'Akurasu OGs Barrier Piercing Weapon List (info/, JP+EN pair): 龍王破山剣・逆鱗断 = "Wrathcleaver"; maintainer decision 2026-09-27 (OG style)', 'Fits in 19 bytes.'),
'天上天下無敵剣': ('Unstoppable Supreme Sword', 'Supreme Sword', 'official', 'Akurasu OGs Mech Database R Series (work/glossary/web/ogs_Mech_Database_R_Series.html): SRX "Unstoppable Supreme Sword"; maintainer decision 2026-09-27 (OG-EN style for SRX/R-1)',
  'Menu short drops "Unstoppable"; the full name belongs in the battle shout (BXCLIST), where there is room.'),
'天上天下念動爆砕剣': ('Unstoppable TK Burst Slash', 'TK Burst Slash', 'official', 'Akurasu OGs Mech Database R Series (work/glossary/web/ogs_Mech_Database_R_Series.html): SRX "Unstoppable TK Burst Slash"; maintainer decision 2026-09-27 (OG-EN style for SRX/R-1)',
  'Menu short drops "Unstoppable"; the full name belongs in the battle shout.'),
'天上天下一撃必殺砲': ('Unstoppable HTB Cannon', 'Unstop. HTB Cannon', 'decided', 'maintainer decision 2026-09-27; OG-EN style (Unstoppable family)',
  'The SRX also has HTBキャノン ("HTB Cannon"), so "Unstoppable" is abbreviated instead of dropped.'),
'天上天下念動破砕剣': ('Unstoppable TK Sword', 'TK Sword', 'official', 'Akurasu OGs Barrier Piercing Weapon List (info/, JP+EN pair): R-1 "Unstoppable TK Sword" = 天上天下念動破砕剣',
  'Full name is 20 bytes; the family rule drops "Unstoppable" in the menu. The OGs Mech Database labels the same R-1 weapon "T-Link Sword" (same stats), but the JP-paired list says Unstoppable TK Sword.'),
'念動集束式レーザーキャノン': ('TK Laser Cannon', None, 'official', 'Akurasu OGs ALL Weapon List (info/, JP+EN pair): 念動収束式Lキャノン = "TK Laser Cannon"', 'OGs official name; fits.'),
'ディスカッター乱舞の太刀': ('Discutter Ranbu no Tachi', 'Discutter Ranbu', 'fan-standard', 'Masou Kishin fandom', 'Keeps the recognizable "Ranbu".'),
'試作型縮退砲': ('Prototype Degeneration Cannon', 'Proto Degen Cannon', 'resolved', 'maintainer decision 2026-09-27: 縮退砲 (Shukutai Hō) = "Degeneration Cannon" (Neo Granzon)',
  'Full name confirmed; short abbreviates Prototype/Degeneration.'),
'4連ミサイルランチャー': ('Quad Missile Launcher', 'Quad Missiles', 'fan-standard', 'convention', '"X Missiles" convention.'),
'ピンポントバリアパンチ': ('Pinpoint Barrier Punch', 'Pinpoint B. Punch', 'official', 'Macross Plus EN', 'The game text has a typo (ピンポント); translate as intended.'),
'小型ミサイル多連ランチャー': ('Multi Mini-Missile Launcher', 'Mini Missile Volley', 'fan-standard', 'convention', 'The previous short "Mini Missile Barrage" was 20 bytes.'),
'ロケットバズーカ射出': ('Rocket Bazooka Launch', 'Rocket Bazooka Fire', 'fan-standard', 'convention', '"Rocket Bazooka" is a separate weapon, so a verb stays (射出 = launch/fire).'),
'ブラックホール・キャノン改': ('Black Hole Cannon Kai', 'Black Hole Cannon', 'fan-standard', 'OG-EN "Black Hole Cannon"', 'Huckebein EX has no plain Black Hole Cannon, so "Kai" can go.'),
'多弾頭ミサイル': ('Multi-Warhead Missile', 'Multi-Head Missile', 'fan-standard', 'convention', 'Alt: "MIRV Missile".'),
}
# former "proposed" rows kept as-is without an external English source
LITERAL = {'クローミサイル','集束ミサイル','格闘','バグ援護攻撃','八手ビームサーベル','ホイールプレッシャー','実弾ライフル',
           '神空剣','紅玉式光線主砲','兵隊','ライトソード','R-コンビネーション','念動シュート','タキス・ミサイル','ゴッドゴーガン把ね撃ち'}
for k in LITERAL: R[k] = (R[k][0], R[k][1], 'accepted-literal') + R[k][3:]
rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
by = {r['jp']: r for r in rows}
missing = [k for k in R if k not in by]
assert not missing, missing
need = [r['jp'] for r in rows if r['status'] == 'proposed' or len(r['en'].encode()) > 19]
assert not [j for j in need if j not in R], [j for j in need if j not in R]
all_en = {r['en']: r['jp'] for r in rows}
out = []
for r in rows:  # keep the order of the source file
    if r['jp'] not in R: continue
    en, short, st, src, why = R[r['jp']]
    short = short or en
    b = len(short.encode('ascii'))
    assert b <= 19, (r['jp'], short, b)
    if short in all_en and all_en[short] != r['jp']:
        sys.exit(f'collision {short} {r["jp"]} {all_en[short]}')
    if en != r['en']:
        why = f'[en changed: was "{r["en"]}"] ' + why
    out.append({'jp': r['jp'], 'en': en, 'en_short': short, 'en_short_bytes': b,
                'status': st, 'source': src, 'rationale': why})
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
from collections import Counter
print(len(out), Counter(o['status'] for o in out))
