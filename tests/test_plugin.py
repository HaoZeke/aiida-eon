"""Plugin surface tests. AiiDA imports are optional so IO CI stays light."""

import pytest

aiida = pytest.importorskip("aiida")


def test_entry_points_resolve():
    from aiida.plugins import (
        CalculationFactory,
        DataFactory,
        ParserFactory,
        WorkflowFactory,
    )

    from aiida_eon.calculations import EonCalculation
    from aiida_eon.data import ConData
    from aiida_eon.parsers import EonParser
    from aiida_eon.workflows import (
        EonAkmcWorkChain,
        EonMinimizeWorkChain,
        EonNebWorkChain,
        EonPrefactorWorkChain,
        EonProcessSearchWorkChain,
        EonSaddleSearchWorkChain,
    )

    assert CalculationFactory("eon") is EonCalculation
    assert ParserFactory("eon") is EonParser
    assert DataFactory("eon.con") is ConData
    assert WorkflowFactory("eon.minimize") is EonMinimizeWorkChain
    assert WorkflowFactory("eon.neb") is EonNebWorkChain
    assert WorkflowFactory("eon.saddle") is EonSaddleSearchWorkChain
    assert WorkflowFactory("eon.process_search") is EonProcessSearchWorkChain
    assert WorkflowFactory("eon.prefactor") is EonPrefactorWorkChain
    assert WorkflowFactory("eon.akmc") is EonAkmcWorkChain


def test_calculation_spec_ports():
    from aiida_eon.calculations import EonCalculation

    spec = EonCalculation.spec()
    assert "parameters" in spec.inputs
    assert "structure" in spec.inputs
    assert "reactant" in spec.inputs
    assert "product" in spec.inputs
    assert "saddle" in spec.inputs
    assert "displacement" in spec.inputs
    assert "direction" in spec.inputs
    assert "potfiles" in spec.inputs
    assert "extra_files" in spec.inputs
    assert "results" in spec.outputs
    assert "scalars" in spec.outputs
    assert spec.inputs["metadata"]["options"]["parser_name"].default == "eon"


def test_workchain_specs_expose_calc():
    from aiida_eon.workflows import EonAkmcWorkChain, EonMinimizeWorkChain, EonNebWorkChain

    min_spec = EonMinimizeWorkChain.spec()
    assert min_spec.inputs["calc"]["structure"].required
    neb_spec = EonNebWorkChain.spec()
    assert neb_spec.inputs["calc"]["product"].required
    akmc_spec = EonAkmcWorkChain.spec()
    assert akmc_spec.inputs["calc"]["structure"].required
    for spec in (min_spec, neb_spec, akmc_spec):
        assert "calc" in spec.inputs
        assert "code" in spec.inputs["calc"]
        assert "parameters" in spec.inputs


def test_elja_helpers():
    from aiida_eon.helpers import ELJA_ACCOUNT, ELJA_QUEUE, ELJA_QUEUE_ANY_CPU, elja_metadata

    meta = elja_metadata(wallclock_seconds=3600, cores=4)
    opts = meta["options"]
    assert opts["queue_name"] == ELJA_QUEUE
    assert ELJA_QUEUE == "s-normal"
    assert ELJA_QUEUE_ANY_CPU == "any_cpu"
    assert opts["account"] == ELJA_ACCOUNT
    assert opts["max_wallclock_seconds"] == 3600
    assert opts["resources"]["num_cores_per_machine"] == 4


def test_version():
    import aiida_eon

    assert aiida_eon.__version__ == "0.3.0"
