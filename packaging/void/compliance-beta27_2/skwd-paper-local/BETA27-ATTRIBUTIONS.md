# beta.27 supplementary attribution

The exact beta.27 source suite and its manifests identify all distributed assets.
This legal revision changes no executable, library or font bytes. The Roboto/Noto
and Nerd Fonts notices in ASSETS.md and assets/ remain applicable; their source
families and modified/subset nature must be retained, not replaced by the merged
font's primary Roboto name.

The changed JP and SC files retain Roboto Project Authors copyright 2011, SIL OFL1.1
and its license URL in their name tables. The subset script additionally identifies
Noto Sans CJK Bold and Noto Sans Symbols2 inputs: credit Google, Adobe and Noto
contributors, with the full Noto/Roboto OFL texts. Exact original input font build
versions were not recorded upstream; this package does not claim to regenerate
those fonts. The delivered font bytes/hashes and the subset script are included
in corresponding sources. Derived names do not use reserved Noto names.

Paper widgets embed the exact Wall base RobotoCondensed-Bold.ttf and retain the
same Roboto OFL notice. The new paper-scene test fonts are generated rectangular
glyph fixtures; build.py imports no third-party font. They are source/test inputs,
not separately bundled commercial font files. No generator was run in this review.

Waycrate registry crates iced_exdevtools0.19.1 and waycrate_xkbkeycode0.19.1:
authors declared by their exact published MIT manifests are Decodertalkers and
Aakash Sen Sharma. The original registry crates have no .cargo_vcs_info.json;
no Git revision is invented. Their checksum matches Cargo.lock, and every shipped
Rust source matches the authenticated registry artifact. The common MIT copyright
notice, Copyright2023 DecodeTalkers, is retained from the suite's matching-author
iced_layershell0.19.1. This is attribution for these Rust sources, not a grant to
redistribute unrelated SDKs. Exact evidence: waycrate-resolution.json.

New dependency notices (including bcdec_rs, rquickjs-core, zune-inflate and pulp)
and all previously retrieved runtime/build/native notices are retained under
compliance/crates, bound by SHA256 in DEPENDENCIES.json. Root workspace declarations
are not represented as evidence of an unrecorded VCS revision.
