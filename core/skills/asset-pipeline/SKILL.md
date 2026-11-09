---
name: asset-pipeline
description: Create, export, import, rename or license-check art and audio. Use for Blender work, moving models into Unreal, Fab or Poly Haven assets, AI-generated meshes, textures, sounds and asset names.
---

# Asset pipeline

Before the jam starts no asset may be created or imported. Stop and say so.

1. Modeling or changes in Blender: delegate to `blender-operator`.
2. Naming, placement and import into Unreal: delegate to `asset-importer`, then `ue-editor-operator` if the import needs the editor.
3. Record every non-original asset: `{{h}} ledger add --kind <sourced|ai-generated|original> --origin <source> --license <license> --path <Content path>`.
4. Finish with the ship skill.

Choose assets with the score in mind: AI-generated and original work is judged, while sourced assets are not scored. Prefer them for what players see most. Before using an AI provider's output, confirm its terms allow commercial use.

Technical details: `references/blender-to-unreal.md`. Naming: `docs/naming-conventions.md`.
