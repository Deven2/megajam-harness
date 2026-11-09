# Blender to Unreal reference

## Folders

| Stage | Path | Notes |
| --- | --- | --- |
| Source file | `Art/Source/<Category>/<Name>.blend` | Heavy. Fetched only on the artist's machine. |
| Export | `Art/Export/<Category>/SM_<Name>.fbx` | One asset per file. |
| Imported | `Content/{{codename}}/Art/<Category>/<Name>/` | Mesh, materials and textures together. |

## Export checklist

- Scene units: metric, unit scale 1.0, 1 Blender unit equals 1 meter.
- Object transforms applied before export. Origin placed at the pivot the game needs.
- FBX settings: `Selected Objects`, `Apply Unit`, forward `-Y`, up `Z`, smoothing `Face`.
- Static collision: add `UCX_<MeshName>` shapes, or generate collision on import.
- Skeletal meshes: export the armature with the mesh, leaf bones off.
- Textures: 2048 maximum unless a person approves more. Name them `T_<Name>_<Suffix>` with suffixes `D`, `N`, `ORM`, `E`.

## Keeping the free LFS quota

- Do not ship on every small tweak. Ship when a version is worth keeping.
- Keep `.blend` compression on.
- Never commit `.blend1` backups or packaged builds.
- Files over 100 MiB need a person's approval.

## Import

Prefer a scripted import through `ue-editor-operator` so names and destinations are repeatable. Check scale against the engine's 1 meter cube after the first import of each category.
