from app.schemas.scenario import (
    CapTableEntry,
    ExitScenario,
    FundingScenario,
    RoundInput,
    ScenarioModelResult,
)


class ScenarioModeler:
    """Pure-Python dilution, cap table, and exit scenario calculator."""

    def model(
        self,
        rounds: list[RoundInput],
        exit_multiples: list[float] | None = None,
    ) -> ScenarioModelResult:
        """Run full scenario model: funding rounds + exit scenarios."""
        if exit_multiples is None:
            exit_multiples = [1.0, 3.0, 5.0, 10.0, 20.0]

        scenarios: list[FundingScenario] = []
        cap_table: list[CapTableEntry] = []

        founder_pct = 1.0
        total_investor_pct = 0.0
        total_pool_pct = 0.0
        last_post_money = 0.0

        for i, round_input in enumerate(rounds):
            scenario = self._model_round(round_input, i + 1, founder_pct)
            scenarios.append(scenario)

            founder_pct = scenario.founder_ownership_after
            dilution = scenario.dilution_pct / 100
            total_investor_pct = total_investor_pct * (1 - dilution) + dilution
            total_pool_pct = round_input.option_pool_pct
            last_post_money = scenario.post_money_valuation

            cap_table.append(CapTableEntry(
                round_label=scenario.round_label,
                founder_pct=round(founder_pct * 100, 2),
                investor_pct=round(total_investor_pct * 100, 2),
                option_pool_pct=round(total_pool_pct * 100, 2),
            ))

        exit_scenarios = self._model_exits(
            last_post_money, founder_pct, exit_multiples,
        )

        return ScenarioModelResult(
            scenarios=scenarios,
            exit_scenarios=exit_scenarios,
            cap_table_progression=cap_table,
        )

    def _model_round(
        self,
        round_input: RoundInput,
        round_number: int,
        founder_pct_before: float,
    ) -> FundingScenario:
        """Calculate a single funding round."""
        raise_amount = round_input.raise_amount
        pre_money = round_input.pre_money_valuation
        pool_pct = round_input.option_pool_pct

        post_money = pre_money + raise_amount
        dilution = raise_amount / post_money

        # Founder ownership after this round = prior * (1 - dilution) * (1 - pool)
        founder_after = founder_pct_before * (1 - dilution) * (1 - pool_pct)

        labels = {1: "Seed", 2: "Series A", 3: "Series B", 4: "Series C", 5: "Series D"}
        round_label = labels.get(round_number, f"Round {round_number}")

        return FundingScenario(
            round_label=round_label,
            raise_amount=raise_amount,
            pre_money_valuation=pre_money,
            post_money_valuation=post_money,
            dilution_pct=round(dilution * 100, 2),
            option_pool_pct=pool_pct,
            founder_ownership_after=round(founder_after, 6),
        )

    @staticmethod
    def _model_exits(
        last_post_money: float,
        founder_pct: float,
        multiples: list[float],
    ) -> list[ExitScenario]:
        """Calculate exit scenarios at various multiples."""
        exits: list[ExitScenario] = []
        for mult in sorted(multiples):
            exit_val = last_post_money * mult
            founder_proceeds = exit_val * founder_pct
            investor_proceeds = exit_val * (1 - founder_pct)
            exits.append(ExitScenario(
                exit_multiple=mult,
                exit_valuation=round(exit_val, 2),
                founder_proceeds=round(founder_proceeds, 2),
                investor_proceeds=round(investor_proceeds, 2),
            ))
        return exits


scenario_modeler = ScenarioModeler()
