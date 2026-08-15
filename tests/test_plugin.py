"""Plugin surface tests. AiiDA imports are optional so IO CI stays light."""

import pytest

aiida = pytest.importorskip("aiida")


def test_entry_points_resolve():
    from aiida.plugins import CalculationFactory, ParserFactory

    calc = CalculationFactory("eon")
    parser = ParserFactory("eon")
    from aiida_eon.calculations import EonCalculation
    from aiida_eon.parsers import EonParser

    assert calc is EonCalculation
    assert parser is EonParser


def test_calculation_spec_ports():
    from aiida_eon.calculations import EonCalculation

    spec = EonCalculation.spec()
    assert "parameters" in spec.inputs
    assert "structure" in spec.inputs
    assert "reactant" in spec.inputs
    assert "results" in spec.outputs
    assert spec.inputs["metadata"]["options"]["parser_name"].default == "eon"
