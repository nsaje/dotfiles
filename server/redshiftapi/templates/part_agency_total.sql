(NVL(SUM({{ p }}effective_cost_nano), 0) + NVL(SUM({{ p }}effective_data_cost_nano), 0) + NVL(SUM({{ p }}license_fee_nano), 0) + NVL(SUM({{ p }}margin_nano), 0))/1000000000.0 {{ alias }}
