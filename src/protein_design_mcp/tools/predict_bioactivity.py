"""
Bioactivity/property prediction tool using ZairaChem (real, published
Ersilia Open Source Initiative AutoML QSAR tool -- see
pipelines/zairachem_runner.py for full provenance and citations).

Scores candidate molecules (e.g. output of a molecule-generation or
docking step elsewhere in this pipeline) against an existing ZairaChem
model -- either one you've trained with train_qsar_model, or a published
pretrained model such as the H3D Centre's malaria/tuberculosis screening
cascade models (github.com/ersilia-os/h3d-screening-cascade-models).
"""

from typing import Any

from protein_design_mcp.pipelines.zairachem_runner import ZairaChemRunner, ZairaChemConfig


async def predict_bioactivity(
    input_csv: str,
    model_dir: str,
    output_dir: str,
) -> dict[str, Any]:
    """
    Predict bioactivity/property class for molecules in input_csv using
    a trained ZairaChem model.

    Args:
        input_csv: CSV containing (at minimum) a SMILES column of
            candidate molecules to score.
        model_dir: Path to a trained ZairaChem model directory (your own,
            or a published pretrained one, e.g. from the H3D Centre
            screening cascade).
        output_dir: Directory ZairaChem will write prediction output into.

    Returns:
        Dict with status, output_dir, and a note on where to find the
        actual predictions file (ZairaChem writes its own output format
        into output_dir -- see pipelines/zairachem_runner.py for why this
        tool doesn't parse/reshape it further).

    Raises:
        ZairaChemError: if the zairachem CLI isn't installed/on PATH, the
            input/model paths don't exist, or the run fails/times out.
    """
    runner = ZairaChemRunner(config=ZairaChemConfig())
    return await runner.predict(input_csv=input_csv, model_dir=model_dir, output_dir=output_dir)
