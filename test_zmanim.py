from pytest import TempdirFactory
import shul_zmanim

def test_make_image(tmpdir_factory:TempdirFactory):
    outdir = tmpdir_factory.mktemp("test_answer").mkdir("outdir")
    result = shul_zmanim.make_image(dest=outdir)
    assert result, f"Expected result to be True-ish: {result}"