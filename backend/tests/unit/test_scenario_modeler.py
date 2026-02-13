import pytest

from app.core.scenario.scenario_modeler import ScenarioModeler
from app.schemas.scenario import RoundInput


@pytest.fixture
def modeler() -> ScenarioModeler:
    return ScenarioModeler()


def test_dilution_calculation_single_round(modeler: ScenarioModeler) -> None:
    """$2M raise at $8M pre-money = 20% dilution."""
    rounds = [RoundInput(raise_amount=2_000_000, pre_money_valuation=8_000_000)]
    result = modeler.model(rounds)

    assert len(result.scenarios) == 1
    scenario = result.scenarios[0]
    assert scenario.post_money_valuation == 10_000_000
    assert scenario.dilution_pct == pytest.approx(20.0, rel=0.01)


def test_multi_round_cap_table_progressive_dilution(modeler: ScenarioModeler) -> None:
    """3-round simulation produces correct progressive dilution."""
    rounds = [
        RoundInput(raise_amount=1_000_000, pre_money_valuation=4_000_000, option_pool_pct=0.10),
        RoundInput(raise_amount=5_000_000, pre_money_valuation=20_000_000, option_pool_pct=0.10),
        RoundInput(raise_amount=15_000_000, pre_money_valuation=60_000_000, option_pool_pct=0.05),
    ]
    result = modeler.model(rounds)

    assert len(result.scenarios) == 3
    assert len(result.cap_table_progression) == 3

    # Founder ownership should decrease with each round
    cap = result.cap_table_progression
    assert cap[0].founder_pct > cap[1].founder_pct > cap[2].founder_pct

    # Final founder % should be significantly less than 100
    assert cap[2].founder_pct < 60
    assert cap[2].founder_pct > 0


def test_exit_scenarios_correct_proceeds(modeler: ScenarioModeler) -> None:
    """Exit at 10x on $10M post-money → correct founder/investor proceeds."""
    rounds = [RoundInput(raise_amount=2_000_000, pre_money_valuation=8_000_000, option_pool_pct=0)]
    result = modeler.model(rounds, exit_multiples=[1.0, 10.0, 20.0])

    assert len(result.exit_scenarios) == 3

    # 10x exit
    exit_10x = next(e for e in result.exit_scenarios if e.exit_multiple == 10.0)
    assert exit_10x.exit_valuation == pytest.approx(100_000_000, rel=0.01)

    # Founder gets 80% (since no option pool, 20% dilution)
    assert exit_10x.founder_proceeds == pytest.approx(80_000_000, rel=0.01)
    assert exit_10x.investor_proceeds == pytest.approx(20_000_000, rel=0.01)
