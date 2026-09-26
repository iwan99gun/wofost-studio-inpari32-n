"""Poin 4b reviewer: Sobol global (S1, ST dengan CI bootstrap) pada model final (8.1 + SLA(N)), dosis 23 & 207 kg N/ha,
target hasil (TWSO) dan LAI maksimum. Rentang +/- ~20 % sekitar nilai kalibrasi (parameter N: rentang literatur)."""
import sys, json
sys.path.insert(0, r"D:\riset_tani_1")


def main():
    import pandas as pd
    import wofost_app  # noqa
    from wofost_app.core.config import SimulationConfig
    from wofost_app.core.weather import build_weather_provider
    from wofost_app.core.simulation import SimulationRunner
    from wofost_app.core.sensitivity import run_sobol
    R = r"D:\riset_tani_1"
    P = [("TSUM1", 1092, 1638), ("TSUM2", 637, 955), ("SPAN", 29.3, 44.0), ("AMAXTB@y", 0.72, 1.08), ("SLATB@ya", 0.96, 1.44),
         ("TDWI", 115, 173), ("NSLA", 0.0, 3.0), ("NLAI", 0.0, 3.0), ("NMAXSO", 0.010, 0.020), ("RGRLAI_MIN_FR", 0.2, 0.9), ("AMAX_SLP", 2.6, 3.9)]
    names = [p[0] for p in P]; bounds = [(p[1], p[2]) for p in P]
    out = {}
    for dose in (23, 207):
        cfg = SimulationConfig.load(f"{R}/data/projects/sujinah2020_sukamandi_mh2017_inpari32_N{dose}_nlv.json")
        run = SimulationRunner(cfg, build_weather_provider(cfg.weather))
        for target in ("TWSO", "LAIMAX"):
            r = run_sobol(run, names, bounds, target, n_base=128, n_workers=8)
            t = r.table.round(3)
            print(f"\n== dosis {dose} N, target {target}\n{t.to_string()}", flush=True)
            out[f"N{dose}_{target}"] = t.reset_index().to_dict("records")
    json.dump({"parameter": P, "n_base": 128, "hasil": out}, open(f"{R}/data/lapangan/sobol_model_final_n.json", "w"), indent=1)
    print("tersimpan", flush=True)


if __name__ == "__main__":
    main()
