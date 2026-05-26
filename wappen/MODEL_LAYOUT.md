# Final model layout for the dual-test setup

This workspace keeps the image-generation assets under `F:\tiroltourismus\wappen`.

## Planned structure

```text
F:\tiroltourismus\wappen\models\flux\flux1-dev-nvfp4.safetensors
F:\tiroltourismus\wappen\models\flux_merged\flux1-dev-fp8.safetensors
F:\tiroltourismus\wappen\models\sd35\sd3.5_medium.safetensors
F:\tiroltourismus\wappen\diffusers-flux-config\
F:\tiroltourismus\wappen\.hf-cache\
F:\tiroltourismus\wappen\img\test-flux\
F:\tiroltourismus\wappen\img\test-sd35\
```

## Current status

- The dual-test script is prepared at `generate_dual_model_tests.py`.
- FLUX requires the actual checkpoint file in the sandboxed workspace.
- SD 3.5 Medium can be pulled from the public Hugging Face repo when the script runs.
- Once both model files are accessible here, the script will create **2 images per model using the same prompt**.

## Prompt used by the test script

> cute anthropomorphic furry mascot logo, clean heraldic emblem, bold geometric shapes, red and gold, white background, centered composition, crisp vector look, no text, no watermark
