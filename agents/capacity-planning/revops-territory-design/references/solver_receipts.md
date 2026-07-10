# External solver receipts

Solver candidates are external evidence, not authority. Require formulation ID, objective-normalization ID, solver and version, seed, raw status, primal/dual bounds, gap, tolerance, time and memory limits, determinism settings, constraint-violation count, and tie policy.

Preserve the solver's raw status. `FEASIBLE` means an incumbent was found; it does not mean optimal. `LIMIT` and `UNDETERMINED` remain `SOLVER_LIMIT`. An `OPTIMAL` label without bounds, gap, tolerance, or zero constraint violations is `POLICY_REQUIRED`.

Do not accept a mixed-unit objective unless its normalization and business meaning were approved before solving. Do not reconstruct a missing objective, choose new weights, rerun a solver, or break ties inside this skill.

Official OR-Tools guidance distinguishes optimal, feasible, infeasible, unbounded, and limit/undetermined outcomes and warns that scaling and tolerances affect solution quality: https://developers.google.com/optimization/lp/lp_advanced
