"""Borg CLI — unified entry point for all borg sub-commands.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

import argparse
import sys
import json

from pathlib import Path

# Lazy imports so --help works even if optional deps are missing


def _cmd_ingest(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s1_path = cli_dir / "pipeline" / "s1_ingestor.py"

    spec = importlib.util.spec_from_file_location("s1_ingestor", s1_path)
    s1_mod = importlib.util.module_from_spec(spec)
    sys.modules["s1_ingestor"] = s1_mod  # register so dataclasses can find __module__
    spec.loader.exec_module(s1_mod)

    S1Ingestor = s1_mod.S1Ingestor

    ingestor = S1Ingestor(vault_path=args.vault)

    if args.stats:
        stats = ingestor.stats()
        print("Ingestor Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return 0

    if args.list:
        results = ingestor.list_results()
        print(f"Results ({len(results)}):")
        for r in results:
            print(
                f"  {r.record_id}: {r.record_kind.value} "
                f"(conf={r.confidence:.2f}, ok={r.ok})"
            )
        return 0

    if args.artifact:
        result = ingestor.ingest_file(
            args.artifact, record_id=args.record_id, algorithm=args.algorithm
        )
        print(f"Ingest result for {result.record_id}:")
        print(f"  Kind: {result.record_kind.value} (conf={result.confidence:.2f})")
        print(f"  Source type: {result.source_type}")
        print(f"  SHA-256: {result.checksums.get('sha256', 'n/a')}")
        print(f"  Size: {result.size_bytes} bytes")
        print(f"  OK: {result.ok}")
        print(f"  Routing: {', '.join(result.suggested_routing) or 'none'}")
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        return 0 if result.ok else 1

    if args.directory:
        results = ingestor.ingest_directory(
            args.directory, glob_pattern=args.glob, algorithm=args.algorithm
        )
        print(f"Ingested {len(results)} files from {args.directory}")
        for r in results:
            status = "✅" if r.ok else "❌"
            print(
                f"  {status} {r.record_id}: {r.record_kind.value} "
                f"(conf={r.confidence:.2f})"
            )
        return 0

    print("No action specified. Use --artifact, --directory, --list, or --stats.")
    return 1


def _cmd_directory(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s3_path = cli_dir / "pipeline" / "s3_directory.py"

    spec = importlib.util.spec_from_file_location("s3_directory", s3_path)
    s3_mod = importlib.util.module_from_spec(spec)
    sys.modules["s3_directory"] = s3_mod  # register so dataclasses can find __module__
    spec.loader.exec_module(s3_mod)

    S3Directory = s3_mod.S3Directory

    directory = S3Directory(vault_path=args.vault)
    directory.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.define_role:
        if not args.name:
            print("--name is required for --define-role")
            return 1
        result = directory.define_role(
            args.name,
            description=args.description,
            domain=args.domain,
            level=args.level,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.define_skill:
        if not args.name:
            print("--name is required for --define-skill")
            return 1
        result = directory.define_skill(
            args.name,
            description=args.description,
            category=args.category,
            difficulty=args.difficulty,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.map:
        if not args.role or not args.skills:
            print("--role and --skills are required for --map")
            return 1
        skills = [s.strip() for s in args.skills.split(",") if s.strip()]
        result = directory.map_role_to_skills(
            args.role,
            skills,
            mapping_type=args.mapping_type,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = directory.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = directory.stats()
        print(json.dumps(stats.to_dict(), indent=2))
        return 0

    if args.test:
        return s3_mod.cmd_test()

    # Default: lookup
    lookup_type = args.lookup.replace("-", "_")
    if lookup_type == "role":
        if not args.name:
            print("--name is required for role lookup")
            return 1
        result = directory.lookup_role(args.name)
    elif lookup_type == "skill":
        if not args.name:
            print("--name is required for skill lookup")
            return 1
        result = directory.lookup_skill(args.name)
    elif lookup_type == "all":
        result = directory.lookup_all(
            domain=args.domain,
            category=args.category,
        )
    elif lookup_type == "orphan_roles":
        result = directory.lookup_orphan_roles()
    elif lookup_type == "orphan_skills":
        result = directory.lookup_orphan_skills()
    else:
        print(f"Unknown lookup type: {args.lookup}")
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def _cmd_skids(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s4_path = cli_dir / "pipeline" / "s4_skids.py"

    spec = importlib.util.spec_from_file_location("s4_skids", s4_path)
    s4_mod = importlib.util.module_from_spec(spec)
    sys.modules["s4_skids"] = s4_mod
    spec.loader.exec_module(s4_mod)

    S4Skids = s4_mod.S4Skids

    skids = S4Skids(vault_path=args.vault)
    skids.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.detect:
        if not args.content:
            print("--content is required for --detect")
            return 1
        result = skids.detect_primitives(
            args.content,
            min_size=args.min_size,
            max_size=args.max_size,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.catalog:
        if not args.catalog_name or not args.primitives_json:
            print("--catalog-name and --primitives-json are required for --catalog")
            return 1
        with open(args.primitives_json) as f:
            primitives_data = json.load(f)
        if isinstance(primitives_data, dict) and "primitives" in primitives_data:
            primitives_data = primitives_data["primitives"]
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = skids.catalog_primitives(
            primitives_data,
            catalog_name=args.catalog_name,
            tags=tags,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = skids.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.search:
        if not args.catalog_name or not args.query:
            print("--catalog-name and --query are required for --search")
            return 1
        result = skids.search_primitives(
            query=args.query,
            catalog_name=args.catalog_name,
            type_filter=args.type_filter,
            min_confidence=args.min_confidence,
            limit=args.limit,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.dedup:
        catalog_names = None
        if args.skids_catalogs:
            catalog_names = [c.strip() for c in args.skids_catalogs.split(",") if c.strip()]
        result = skids.dedup_primitives(
            catalog_names=catalog_names,
            similarity_threshold=args.similarity_threshold,
            keep_strategy=args.keep_strategy,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = skids.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = skids.stats()
        print(json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s4_mod.cmd_test()

    print("No action specified. Use --detect, --catalog, --search, --dedup, --stats, or --test.")
    return 1


def _cmd_pipeline_test(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    pipeline_dir = cli_dir / "pipeline"

    s1_path = pipeline_dir / "s1_ingestor.py"
    s2_path = pipeline_dir / "s2_profiler.py"
    s3_path = pipeline_dir / "s3_directory.py"
    s4_path = pipeline_dir / "s4_skids.py"
    s5_path = pipeline_dir / "s5_decompose.py"
    s6_path = pipeline_dir / "s6_tacit.py"
    s7_path = pipeline_dir / "s7_dedup.py"
    s8_path = pipeline_dir / "s8_measure.py"
    s9_path = pipeline_dir / "s9_search.py"

    def _load_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod  # register so dataclasses can find __module__
        spec.loader.exec_module(mod)
        return mod

    s1_mod = _load_module("s1_ingestor", s1_path)
    s2_mod = _load_module("s2_profiler", s2_path)
    s3_mod = _load_module("s3_directory", s3_path)
    s4_mod = _load_module("s4_skids", s4_path)
    s5_mod = _load_module("s5_decompose", s5_path)
    s6_mod = _load_module("s6_tacit", s6_path)
    s7_mod = _load_module("s7_dedup", s7_path)
    s8_mod = _load_module("s8_measure", s8_path)
    s9_mod = _load_module("s9_search", s9_path)

    print("Borg Pipeline — Self-Test Suite")
    print("=" * 50)

    s1_result = s1_mod.cmd_test()
    print()
    s2_result = s2_mod.cmd_test()
    print()
    s3_result = s3_mod.cmd_test()
    print()
    s4_result = s4_mod.cmd_test()
    print()
    s5_result = s5_mod.cmd_test()
    print()
    s6_result = s6_mod.cmd_test()
    print()
    s7_result = s7_mod.cmd_test()
    print()
    s8_result = s8_mod.cmd_test()
    print()
    s9_result = s9_mod.cmd_test()

    if (
        s1_result == 0
        and s2_result == 0
        and s3_result == 0
        and s4_result == 0
        and s5_result == 0
        and s6_result == 0
        and s7_result == 0
        and s8_result == 0
        and s9_result == 0
    ):
        print("\n✅ ALL PIPELINE TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME PIPELINE TESTS FAILED")
        return 1


def _cmd_decompose(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s5_path = cli_dir / "pipeline" / "s5_decompose.py"

    spec = importlib.util.spec_from_file_location("s5_decompose", s5_path)
    s5_mod = importlib.util.module_from_spec(spec)
    sys.modules["s5_decompose"] = s5_mod
    spec.loader.exec_module(s5_mod)

    S5Decompose = s5_mod.S5Decompose

    decompose = S5Decompose(vault_path=args.vault)
    decompose.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.detect:
        if not args.content:
            print("--content is required for --detect")
            return 1
        result = decompose.detect_composites(
            args.content,
            min_size=args.min_size,
            apply=not dry_run,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.decompose:
        if not args.composite_id:
            print("--composite-id is required for --decompose")
            return 1
        units_data = None
        if args.units_json:
            with open(args.units_json) as f:
                units_data = json.load(f)
        deps = None
        if args.deps_json:
            with open(args.deps_json) as f:
                deps_data = json.load(f)
                if isinstance(deps_data, list):
                    deps = [tuple(d) for d in deps_data]
        result = decompose.decompose(
            args.composite_id,
            units_data,
            deps,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = decompose.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.execution_order:
        if not args.composite_id:
            print("--composite-id is required for --execution-order")
            return 1
        result = decompose.execution_order(
            args.composite_id,
            parallelizable=args.parallelizable,
            max_parallel=args.max_parallel,
            apply=not dry_run,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.stats:
        stats = decompose.stats()
        print(json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s5_mod.cmd_test()

    print("No action specified. Use --detect, --decompose, --execution-order, --stats, or --test.")
    return 1


def _cmd_tacit(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s6_path = cli_dir / "pipeline" / "s6_tacit.py"

    spec = importlib.util.spec_from_file_location("s6_tacit", s6_path)
    s6_mod = importlib.util.module_from_spec(spec)
    sys.modules["s6_tacit"] = s6_mod
    spec.loader.exec_module(s6_mod)

    S6Tacit = s6_mod.S6Tacit

    tacit = S6Tacit(vault_path=args.vault)
    tacit.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.capture:
        if not args.situation or not args.decision or not args.reasoning:
            print("--situation, --decision, and --reasoning are required for --capture")
            return 1
        context_factors = [f.strip() for f in args.context_factors.split(",") if f.strip()]
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = tacit.capture_judgment(
            situation=args.situation,
            decision=args.decision,
            reasoning=args.reasoning,
            context_factors=context_factors,
            outcome=args.outcome or None,
            confidence=args.confidence,
            tags=tags,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = tacit.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.analyze:
        if not args.situation:
            print("--situation is required for --analyze")
            return 1
        similar = [f.strip() for f in args.similar_decisions.split(",") if f.strip()]
        result = tacit.analyze_nuance(
            situation=args.situation,
            similar_decisions=similar,
            context=args.context or None,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.route:
        if not args.situation or not args.decision_type or not args.impact_level or not args.reversibility or not args.time_pressure:
            print("--situation, --decision-type, --impact-level, --reversibility, and --time-pressure are required for --route")
            return 1
        expertise = [f.strip() for f in args.available_expertise.split(",") if f.strip()]
        result = tacit.route_judgment(
            situation=args.situation,
            decision_type=args.decision_type,
            impact_level=args.impact_level,
            reversibility=args.reversibility,
            time_pressure=args.time_pressure,
            available_expertise=expertise,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.preserve:
        if not args.judgment_id or not args.situation_key:
            print("--judgment-id and --situation-key are required for --preserve")
            return 1
        review_triggers = [f.strip() for f in args.review_triggers.split(",") if f.strip()]
        related = [f.strip() for f in args.related_judgments.split(",") if f.strip()]
        result = tacit.preserve_context(
            judgment_id=args.judgment_id,
            situation_key=args.situation_key,
            applicability_scope=args.applicability_scope,
            review_triggers=review_triggers,
            related_judgments=related,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = tacit.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = tacit.stats()
        print(json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s6_mod.cmd_test()

    print("No action specified. Use --capture, --analyze, --route, --preserve, --stats, or --test.")
    return 1


def _cmd_dedup(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s7_path = cli_dir / "pipeline" / "s7_dedup.py"

    spec = importlib.util.spec_from_file_location("s7_dedup", s7_path)
    s7_mod = importlib.util.module_from_spec(spec)
    sys.modules["s7_dedup"] = s7_mod
    spec.loader.exec_module(s7_mod)

    S7Dedup = s7_mod.S7Dedup

    dedup = S7Dedup(vault_path=args.vault)
    dedup.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.similarity:
        if not args.record_a or not args.record_b:
            print("--record-a and --record-b are required for --similarity")
            return 1
        import json as _json
        try:
            record_a = _json.loads(args.record_a)
        except _json.JSONDecodeError:
            record_a = {"content": args.record_a}
        try:
            record_b = _json.loads(args.record_b)
        except _json.JSONDecodeError:
            record_b = {"content": args.record_b}
        fields = [f.strip() for f in args.fields.split(",") if f.strip()] or None
        weights = _json.loads(args.weights) if args.weights else None
        result = dedup.compute_similarity(record_a, record_b, fields, weights)
        print(_json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.canonicalize:
        if not args.records_json:
            print("--records-json is required for --canonicalize")
            return 1
        import json as _json
        with open(args.records_json) as f:
            records = _json.load(f)
        result = dedup.canonicalize(
            records,
            similarity_threshold=args.similarity_threshold,
            merge_strategy=args.merge_strategy,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = dedup.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.merge_resolve:
        if not args.field_name or not args.values:
            print("--field-name and --values are required for --merge-resolve")
            return 1
        import json as _json
        values = _json.loads(args.values)
        confidences = _json.loads(args.confidences) if args.confidences else None
        sources = _json.loads(args.sources) if args.sources else None
        result = dedup.merge_resolve(args.field_name, values, confidences, sources)
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = dedup.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.diversity:
        if not args.records_json or not args.dimensions:
            print("--records-json and --dimensions are required for --diversity")
            return 1
        import json as _json
        with open(args.records_json) as f:
            records = _json.load(f)
        dimensions = [d.strip() for d in args.dimensions.split(",") if d.strip()]
        result = dedup.promote_diversity(
            records,
            diversity_dimensions=dimensions,
            max_per_dimension=args.max_per_dimension,
            min_representation=args.min_representation,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = dedup.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = dedup.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s7_mod.cmd_test()

    print("No action specified. Use --similarity, --canonicalize, --merge-resolve, --diversity, --stats, or --test.")
    return 1


def _cmd_measure(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s8_path = cli_dir / "pipeline" / "s8_measure.py"

    spec = importlib.util.spec_from_file_location("s8_measure", s8_path)
    s8_mod = importlib.util.module_from_spec(spec)
    sys.modules["s8_measure"] = s8_mod
    spec.loader.exec_module(s8_mod)

    S8Measure = s8_mod.S8Measure
    TestDesign = s8_mod.TestDesign
    TestExecution = s8_mod.TestExecution
    _test_id = s8_mod._test_id

    measure = S8Measure(vault_path=args.vault)
    measure.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.design:
        if not args.claim:
            print("--claim is required for --design")
            return 1
        import json as _json
        record = None
        if args.record:
            try:
                record = _json.loads(args.record)
            except _json.JSONDecodeError:
                record = {"content": args.record}
        success_criteria = [c.strip() for c in args.success_criteria.split(",") if c.strip()]
        result = measure.design_test(
            claim=args.claim,
            record=record,
            test_type=args.test_type,
            success_criteria=success_criteria,
            constraints=args.constraints,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = measure.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.execute:
        if not args.hypothesis:
            print("--hypothesis is required for --execute")
            return 1
        design = TestDesign(
            hypothesis=args.hypothesis,
            test_type="accuracy",
            success_criteria=[],
        )
        result = measure.execute_test(
            design,
            environment=args.environment,
            execution_params={"iterations": args.iterations, "timeout": args.timeout},
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = measure.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.analyze:
        if not args.hypothesis:
            print("--hypothesis is required for --analyze")
            return 1
        design = TestDesign(
            hypothesis=args.hypothesis,
            test_type="accuracy",
            success_criteria=[],
        )
        exec_obj = TestExecution(test_id=_test_id(args.hypothesis), status="passed")
        baseline = None
        if args.baseline_hypothesis:
            baseline_id = _test_id(args.baseline_hypothesis)
            if baseline_id in measure._executions:
                baseline = measure._executions[baseline_id]
        result = measure.analyze_test(exec_obj, design, baseline)
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = measure.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.store_metrics:
        if not args.test_id or not args.metrics_json:
            print("--test-id and --metrics-json are required for --store-metrics")
            return 1
        import json as _json
        try:
            metrics = _json.loads(args.metrics_json)
        except _json.JSONDecodeError:
            metrics = {"value": float(args.metrics_json)}
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = measure.store_metrics(
            test_id=args.test_id,
            metrics=metrics,
            tags=tags,
            timestamp=args.timestamp or None,
            context=args.context,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = measure.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = measure.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s8_mod.cmd_test()

    print("No action specified. Use --design, --execute, --analyze, --store-metrics, --stats, or --test.")
    return 1


def _cmd_search(args: argparse.Namespace) -> int:
    import importlib.util

    cli_dir = Path(__file__).resolve().parent
    s9_path = cli_dir / "pipeline" / "s9_search.py"

    spec = importlib.util.spec_from_file_location("s9_search", s9_path)
    s9_mod = importlib.util.module_from_spec(spec)
    sys.modules["s9_search"] = s9_mod
    spec.loader.exec_module(s9_mod)

    S9Search = s9_mod.S9Search

    search = S9Search(vault_path=args.vault)
    search.load_from_vault()

    dry_run = args.dry_run and not args.apply

    import json as _json

    if args.retrieve:
        if not args.query:
            print("--query is required for --retrieve")
            return 1
        catalogs = [c.strip() for c in args.catalogs.split(",") if c.strip()] or None
        filters = _json.loads(args.filters) if args.filters else None
        result = search.retrieve(
            query=args.query,
            catalogs=catalogs,
            filters=filters,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = search.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.route:
        if not args.query:
            print("--query is required for --route")
            return 1
        targets = [t.strip() for t in args.targets.split(",") if t.strip()] or None
        result = search.route(
            query=args.query,
            query_type=args.query_type,
            context=args.context,
            available_targets=targets,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = search.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.rank:
        if not args.query or not args.results_json:
            print("--query and --results-json are required for --rank")
            return 1
        with open(args.results_json) as f:
            results = _json.load(f)
        user_context = _json.loads(args.user_context) if args.user_context else None
        result = search.rank(
            results=results,
            query=args.query,
            user_context=user_context,
            diversity=not args.no_diversity,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = search.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.cache:
        if not args.query:
            print("--query is required for --cache")
            return 1
        results = None
        if args.results_json_cache:
            with open(args.results_json_cache) as f:
                results = _json.load(f)
        result = search.cache(
            operation=args.cache_op,
            query=args.query,
            results=results,
            cache_ttl=args.cache_ttl,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            p = search.save_to_vault(apply=True)
            if p:
                print(f"\nSaved to: {p}")
        return 0 if result["ok"] else 1

    if args.stats:
        stats = search.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    if args.test:
        return s9_mod.cmd_test()

    print("No action specified. Use --retrieve, --route, --rank, --cache, --stats, or --test.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Borg — artifact intake / TRUST / ART adapters, pipeline agents",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )

    sub = parser.add_subparsers(dest="command")

    # Ingest command
    p_ingest = sub.add_parser("ingest", help="S1 Ingestor — unpack, checksum, classify")
    p_ingest.add_argument("--artifact", help="Single artifact file to ingest")
    p_ingest.add_argument("--record-id", help="Record ID (defaults to filename)")
    p_ingest.add_argument(
        "--algorithm", default="sha256", help="Hash algorithm (default: sha256)"
    )
    p_ingest.add_argument("--directory", help="Directory to ingest (all files)")
    p_ingest.add_argument("--glob", default="**/*", help="Glob pattern")
    p_ingest.add_argument("--list", action="store_true", help="List all results")
    p_ingest.add_argument("--stats", action="store_true", help="Show statistics")
    p_ingest.add_argument(
        "--test", action="store_true", help="Run S1 Ingestor self-tests"
    )

    # Directory command (S3)
    p_dir = sub.add_parser("directory", help="S3 Directory — Roles × Skills ontology")
    p_dir.add_argument(
        "--define-role", action="store_true", help="Define a new role (with --name)"
    )
    p_dir.add_argument("--name", help="Role or skill name")
    p_dir.add_argument("--description", default="", help="Description")
    p_dir.add_argument("--domain", default="", help="Role domain")
    p_dir.add_argument("--level", default="", help="Role level")
    p_dir.add_argument(
        "--define-skill", action="store_true", help="Define a new skill (with --name)"
    )
    p_dir.add_argument("--category", default="", help="Skill category")
    p_dir.add_argument("--difficulty", default="", help="Skill difficulty")
    p_dir.add_argument(
        "--map", action="store_true", help="Map role to skills (--role + --skills)"
    )
    p_dir.add_argument("--role", help="Role name for mapping")
    p_dir.add_argument(
        "--skills", help="Comma-separated skill names for mapping"
    )
    p_dir.add_argument(
        "--mapping-type",
        default="add",
        choices=["add", "replace"],
        help="add (default) or replace",
    )
    p_dir.add_argument(
        "--lookup",
        choices=["role", "skill", "all", "orphan-roles", "orphan-skills"],
        default="all",
        help="Lookup type (default: all)",
    )
    p_dir.add_argument("--stats", action="store_true", help="Show directory statistics")
    p_dir.add_argument(
        "--test", action="store_true", help="Run S3 Directory self-tests"
    )

    # Skids command (S4)
    p_skids = sub.add_parser("skids", help="S4 Skids — Find L0 primitives")
    p_skids.add_argument(
        "--detect", action="store_true", help="Detect L0 primitives from content"
    )
    p_skids.add_argument("--content", help="Content to analyze")
    p_skids.add_argument("--min-size", type=int, default=20, help="Minimum primitive size")
    p_skids.add_argument("--max-size", type=int, default=500, help="Maximum primitive size")
    p_skids.add_argument(
        "--catalog", action="store_true", help="Catalog primitives into searchable index"
    )
    p_skids.add_argument("--catalog-name", help="Catalog name")
    p_skids.add_argument(
        "--primitives-json", help="JSON file with primitives list"
    )
    p_skids.add_argument("--tags", default="", help="Comma-separated tags")
    p_skids.add_argument(
        "--search", action="store_true", help="Search primitives in a catalog"
    )
    p_skids.add_argument("--query", help="Search query")
    p_skids.add_argument("--type-filter", help="Filter by primitive type")
    p_skids.add_argument("--min-confidence", type=float, help="Minimum confidence (0.0-1.0)")
    p_skids.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_skids.add_argument(
        "--dedup", action="store_true", help="Deduplicate primitives across catalogs"
    )
    p_skids.add_argument(
        "--skids-catalogs", help="Comma-separated catalog names (default: all)"
    )
    p_skids.add_argument(
        "--similarity-threshold", type=float, default=0.9, help="Similarity threshold"
    )
    p_skids.add_argument(
        "--keep-strategy",
        default="highest_confidence",
        choices=["highest_confidence", "first_seen"],
        help="Keep strategy (default: highest_confidence)",
    )
    p_skids.add_argument("--stats", action="store_true", help="Show skids statistics")
    p_skids.add_argument(
        "--test", action="store_true", help="Run S4 Skids self-tests"
    )

    # Decompose command (S5)
    p_decompose = sub.add_parser(
        "decompose", help="S5 Decompose — Composites → DAGs"
    )
    p_decompose.add_argument(
        "--detect", action="store_true", help="Detect composite tasks from content"
    )
    p_decompose.add_argument("--content", help="Content to analyze")
    p_decompose.add_argument(
        "--min-size", type=int, default=100, help="Minimum composite size"
    )
    p_decompose.add_argument(
        "--decompose", action="store_true", help="Decompose a composite into DAG"
    )
    p_decompose.add_argument(
        "--composite-id", help="Composite ID to decompose or get execution order for"
    )
    p_decompose.add_argument(
        "--units-json", help="JSON file with units list"
    )
    p_decompose.add_argument(
        "--deps-json", help="JSON file with dependency pairs list"
    )
    p_decompose.add_argument(
        "--execution-order", action="store_true", help="Get execution order from DAG"
    )
    p_decompose.add_argument(
        "--parallelizable",
        action="store_true",
        default=True,
        help="Identify parallelizable units",
    )
    p_decompose.add_argument(
        "--max-parallel", type=int, default=3, help="Max parallel units per wave"
    )
    p_decompose.add_argument(
        "--stats", action="store_true", help="Show decompose statistics"
    )
    p_decompose.add_argument(
        "--test", action="store_true", help="Run S5 Decompose self-tests"
    )

    # Tacit command (S6)
    p_tacit = sub.add_parser("tacit", help="S6 Tacit — Judgment and nuance")
    p_tacit.add_argument(
        "--capture", action="store_true", help="Capture a tacit judgment call"
    )
    p_tacit.add_argument("--situation", help="Situation description")
    p_tacit.add_argument("--decision", help="Decision made")
    p_tacit.add_argument("--reasoning", help="Reasoning behind decision")
    p_tacit.add_argument(
        "--context-factors", default="", help="Comma-separated context factors"
    )
    p_tacit.add_argument("--outcome", default="", help="Outcome if known")
    p_tacit.add_argument(
        "--confidence", type=float, default=0.5, help="Confidence level (0.0-1.0)"
    )
    p_tacit.add_argument("--tags", default="", help="Comma-separated tags")
    p_tacit.add_argument(
        "--analyze", action="store_true", help="Analyze nuance in a situation"
    )
    p_tacit.add_argument(
        "--similar-decisions", default="", help="Comma-separated similar decisions"
    )
    p_tacit.add_argument("--context", default="", help="Additional context")
    p_tacit.add_argument(
        "--route", action="store_true", help="Route a decision based on context"
    )
    p_tacit.add_argument(
        "--decision-type", required=False, help="Type of decision"
    )
    p_tacit.add_argument(
        "--impact-level", required=False, help="Impact level (low/medium/high/critical)"
    )
    p_tacit.add_argument(
        "--reversibility", required=False, help="Reversibility (fully/partially/not)"
    )
    p_tacit.add_argument(
        "--time-pressure",
        required=False,
        help="Time pressure (plenty/moderate/urgent/immediate)",
    )
    p_tacit.add_argument(
        "--available-expertise", default="", help="Comma-separated expertise"
    )
    p_tacit.add_argument(
        "--preserve", action="store_true", help="Preserve context for future decisions"
    )
    p_tacit.add_argument(
        "--judgment-id", help="Judgment ID to preserve context for"
    )
    p_tacit.add_argument(
        "--situation-key", help="Key phrase for lookup"
    )
    p_tacit.add_argument(
        "--applicability-scope", default="moderate", help="Scope (narrow/moderate/broad)"
    )
    p_tacit.add_argument(
        "--review-triggers", default="", help="Comma-separated review triggers"
    )
    p_tacit.add_argument(
        "--related-judgments", default="", help="Comma-separated related judgment IDs"
    )
    p_tacit.add_argument("--stats", action="store_true", help="Show tacit statistics")
    p_tacit.add_argument(
        "--test", action="store_true", help="Run S6 Tacit self-tests"
    )

    # Dedup command (S7)
    p_dedup = sub.add_parser("dedup", help="S7 Dedup — Canonicalize + diversity")
    p_dedup.add_argument(
        "--similarity", action="store_true", help="Compute similarity between two records"
    )
    p_dedup.add_argument("--record-a", help="JSON file or JSON string for record A")
    p_dedup.add_argument("--record-b", help="JSON file or JSON string for record B")
    p_dedup.add_argument("--fields", default="", help="Comma-separated fields to compare")
    p_dedup.add_argument("--weights", default="", help="JSON string for field weights")
    p_dedup.add_argument(
        "--canonicalize", action="store_true", help="Canonicalize duplicate records"
    )
    p_dedup.add_argument("--records-json", help="JSON file with records list")
    p_dedup.add_argument(
        "--similarity-threshold", type=float, default=0.85, help="Similarity threshold"
    )
    p_dedup.add_argument(
        "--merge-strategy", default="union", help="Merge strategy"
    )
    p_dedup.add_argument(
        "--merge-resolve", action="store_true", help="Resolve a merge conflict"
    )
    p_dedup.add_argument("--field-name", help="Field name")
    p_dedup.add_argument(
        "--values", help="JSON list of values"
    )
    p_dedup.add_argument(
        "--confidences", default="", help="JSON list of confidences"
    )
    p_dedup.add_argument(
        "--sources", default="", help="JSON list of sources"
    )
    p_dedup.add_argument(
        "--diversity", action="store_true", help="Promote diversity across records"
    )
    p_dedup.add_argument(
        "--dimensions", default="", help="Comma-separated diversity dimensions"
    )
    p_dedup.add_argument(
        "--max-per-dimension", type=int, default=3, help="Max records per dimension value"
    )
    p_dedup.add_argument(
        "--min-representation", type=int, default=1, help="Min records per dimension value"
    )
    p_dedup.add_argument("--stats", action="store_true", help="Show dedup statistics")
    p_dedup.add_argument(
        "--test", action="store_true", help="Run S7 Dedup self-tests"
    )

    # Measure command (S8)
    p_measure = sub.add_parser("measure", help="S8 Measure — Empirical tests")
    p_measure.add_argument(
        "--design", action="store_true", help="Design an empirical test"
    )
    p_measure.add_argument("--claim", required=False, help="Claim or hypothesis to test")
    p_measure.add_argument(
        "--record", help="JSON file or string for the record being tested"
    )
    p_measure.add_argument(
        "--test-type", default="accuracy", help="Type of test (accuracy/performance/robustness/validity/reliability)"
    )
    p_measure.add_argument(
        "--success-criteria", default="", help="Comma-separated success criteria"
    )
    p_measure.add_argument(
        "--constraints", default="", help="Constraints on the test"
    )
    p_measure.add_argument(
        "--execute", action="store_true", help="Execute an empirical test"
    )
    p_measure.add_argument(
        "--hypothesis", required=False, help="Hypothesis from test design"
    )
    p_measure.add_argument(
        "--environment", default="default", help="Test environment"
    )
    p_measure.add_argument("--iterations", type=int, default=1, help="Number of iterations")
    p_measure.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    p_measure.add_argument(
        "--analyze", action="store_true", help="Analyze test results"
    )
    p_measure.add_argument(
        "--baseline-hypothesis", default="", help="Baseline hypothesis for comparison"
    )
    p_measure.add_argument(
        "--store-metrics", action="store_true", help="Store test metrics"
    )
    p_measure.add_argument("--test-id", help="Test ID")
    p_measure.add_argument(
        "--metrics-json", help="JSON file or string with metrics"
    )
    p_measure.add_argument("--tags", default="", help="Comma-separated tags")
    p_measure.add_argument("--timestamp", default="", help="ISO 8601 timestamp")
    p_measure.add_argument("--context", default="", help="Additional context")
    p_measure.add_argument("--stats", action="store_true", help="Show measure statistics")
    p_measure.add_argument(
        "--test", action="store_true", help="Run S8 Measure self-tests"
    )

    # Search command (S9)
    p_search = sub.add_parser("search", help="S9 Search — Retrieval + routing")
    p_search.add_argument(
        "--retrieve", action="store_true", help="Retrieve relevant records"
    )
    p_search.add_argument("--query", help="Search query")
    p_search.add_argument(
        "--catalogs", default="", help="Comma-separated catalog names"
    )
    p_search.add_argument(
        "--filters", default="", help="JSON string for filters"
    )
    p_search.add_argument("--top-k", type=int, default=10, help="Max results")
    p_search.add_argument(
        "--min-score", type=float, default=0.0, help="Minimum relevance score"
    )
    p_search.add_argument(
        "--route", action="store_true", help="Route a search query"
    )
    p_search.add_argument(
        "--query-type", default="exploration", help="Type of query"
    )
    p_search.add_argument("--context", default="", help="Additional context")
    p_search.add_argument(
        "--targets", default="", help="Comma-separated available targets"
    )
    p_search.add_argument(
        "--rank", action="store_true", help="Rank and re-rank results"
    )
    p_search.add_argument(
        "--results-json", help="JSON file with results list"
    )
    p_search.add_argument(
        "--user-context", default="", help="JSON string for user context"
    )
    p_search.add_argument(
        "--no-diversity", action="store_true", help="Disable diversity filtering"
    )
    p_search.add_argument(
        "--cache", action="store_true", help="Manage search result cache"
    )
    p_search.add_argument(
        "--cache-op", default="retrieve", help="store|retrieve|invalidate|stats"
    )
    p_search.add_argument(
        "--results-json-cache", help="JSON file with results to store"
    )
    p_search.add_argument(
        "--cache-ttl", type=int, default=3600, help="Cache TTL in seconds"
    )
    p_search.add_argument("--stats", action="store_true", help="Show search statistics")
    p_search.add_argument(
        "--test", action="store_true", help="Run S9 Search self-tests"
    )

    # Pipeline test command
    p_pipe_test = sub.add_parser(
        "pipeline-test", help="Run all pipeline agent self-tests (S1–S10)"
    )

    # Layout commands (stubs for future phases)
    p_layout = sub.add_parser("layout", help="Repo layout management")
    p_layout.add_argument(
        "--layout-create", action="store_true", help="Create repo layout (§19.1)"
    )
    p_layout.add_argument(
        "--layout-list", action="store_true", help="List layout directories"
    )

    # Model validation (stub)
    p_model = sub.add_parser("model", help="Record schema validation")
    p_model.add_argument(
        "--model-validate", action="store_true", help="Validate record schema"
    )

    # TRUST scan (stub)
    p_trust = sub.add_parser("trust", help="TRUST security scan")
    p_trust.add_argument(
        "--trust-scan", action="store_true", help="Run TRUST checks"
    )

    # ART absorb (stub)
    p_art = sub.add_parser("art", help="ART absorption adapters")
    p_art.add_argument(
        "--art-absorb", action="store_true", help="Absorb artifacts via ART adapters"
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "ingest":
        return _cmd_ingest(args)

    if args.command == "directory":
        return _cmd_directory(args)

    if args.command == "skids":
        return _cmd_skids(args)

    if args.command == "decompose":
        return _cmd_decompose(args)

    if args.command == "tacit":
        return _cmd_tacit(args)

    if args.command == "dedup":
        return _cmd_dedup(args)

    if args.command == "measure":
        return _cmd_measure(args)

    if args.command == "search":
        return _cmd_search(args)

    if args.command == "pipeline-test":
        return _cmd_pipeline_test(args)

    if args.command == "layout":
        if args.layout_create:
            print("Layout creation — coming in Phase 1 (already released)")
            return 0
        if args.layout_list:
            print("Layout listing — coming in Phase 1 (already released)")
            return 0
        print("Use --layout-create or --layout-list")
        return 1

    if args.command == "model":
        if args.model_validate:
            print("Model validation — coming in Phase 1 (already released)")
            return 0
        print("Use --model-validate")
        return 1

    if args.command == "trust":
        if args.trust_scan:
            print("TRUST scan — coming in Phase 1 (already released)")
            return 0
        print("Use --trust-scan")
        return 1

    if args.command == "art":
        if args.art_absorb:
            print("ART absorb — coming in Phase 1 (already released)")
            return 0
        print("Use --art-absorb")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
