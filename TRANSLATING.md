# Translate *Super Robot Wars Alpha* into your language

Everything this project used to translate *Super Robot Taisen Alpha* (PlayStation, 2000) into English is here: the
tools that extract and rebuild every text format, the variable-width font, the menu relocator, the validator, the
build pipeline that produces a patch, and the full English script as a starting point. You are welcome to use all of
it to make a translation into **your own language**.

## The three requirements

There are only three. Please respect them:

> **1. Fork this project.**
> Use GitHub's **Fork** button on
> [Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver](https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver)
> and work in your fork. Don't re-upload the files as a new, unrelated repository: the fork link is how players and
> other translators find the original project and its fixes.
>
> **2. Do not modify the thanks / dedication screen.**
> It is the screen shown at boot right after the copyright notice: a dedication and two QR codes (GitHub and
> Buy Me a Coffee). Leave `work/tools/src/dedicatoria.py`, `work/patches/dedicatoria.asm` and the `dedicatoria`
> build stage exactly as they are, and don't skip that stage in your releases. The kit's CI checks it
> (`work/tools/ci_check.sh dedication`).
>
> **3. Link my Buy Me a Coffee page: <https://buymeacoffee.com/srwa_en>**
> Put the link in your fork's `README.md` and on every page where you publish or announce your patch (GitHub release
> notes, forum posts, download pages). Keep `.github/FUNDING.yml` as it is, so your fork's **Sponsor** button points
> there too.

That's all. Credit yourself and your team wherever you like: your README, your release notes, your announcements.

A reminder that is not a requirement, just the law: publish **patches only** (`.xdelta`). Never upload disc images
(`.bin`, `.cue`, `.iso`), the BIOS or files extracted from the game. The kit is built so that you never have to: it
contains no game data, and its CI refuses to let any slip into your repository.

## Start here

**[docs/TRANSLATION_GUIDE.md](docs/TRANSLATION_GUIDE.md)**: the complete manual, from forking and setting up to
publishing your patch.

In short (Linux or WSL2, with your own dump of the Japanese disc):

```bash
git clone https://github.com/<you>/Super-Robot-Wars-Alpha-PSX-English-Ver.git
cd Super-Robot-Wars-Alpha-PSX-English-Ver
# put "Super Robot Taisen Alpha (Japan) (v1.0).bin" and ".cue" here, then:
work/tools/kit_setup.sh --tools
work/.venv/bin/python work/tools/src/kit.py pivot
```

<a href="https://www.buymeacoffee.com/Srwa_en" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
