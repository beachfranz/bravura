"""CLI for research planning, execution, review and design approval."""
import argparse
import json
import sys
from pathlib import Path
from . import contracts as c
from . import packet, workflow


def read(path):
    return json.loads(Path(path).read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bravura")
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan", help="Print the five bounded research assignments")
    plan.add_argument("brief")
    run = sub.add_parser("research", help="Run replay fixtures or a trusted external agent adapter")
    run.add_argument("brief")
    adapter = run.add_mutually_exclusive_group(required=True)
    adapter.add_argument("--replay", metavar="DIRECTORY")
    adapter.add_argument("--agent-command", help='JSON argument array, e.g. ["python", "adapter.py"]')
    run.add_argument("--out", required=True)
    generate = sub.add_parser("generate", help="Generate an approved Apple v0.2 dataset and answer key")
    generate.add_argument("config")
    generate.add_argument("--approval", required=True)
    generate.add_argument("--out", required=True)
    validate = sub.add_parser("validate", help="Validate a complete authoring bundle")
    validate.add_argument("bundle")
    render = sub.add_parser("render", help="Build a review packet from a validated bundle")
    render.add_argument("bundle")
    render.add_argument("--out", required=True)
    approve = sub.add_parser("approve", help="Explicitly record a local user's design approval")
    approve.add_argument("bundle")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--note", required=True)
    approve.add_argument("--out", required=True)
    verify = sub.add_parser("verify-approval")
    verify.add_argument("approval")
    verify.add_argument("bundle")
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            spec = c.brief(read(args.brief))
            print(json.dumps([workflow.request(role, spec, {}) for role in workflow.ROLES], indent=2))
        elif args.action == "research":
            backend = workflow.Replay(args.replay) if args.replay else workflow.Command(json.loads(args.agent_command))
            workflow.run(read(args.brief), backend, args.out)
            print(f"Review packet: {Path(args.out) / 'review.html'} ({backend.mode}; awaiting user review)")
        elif args.action == "generate":
            from .release import generate
            print(json.dumps(generate(read(args.config), read(args.approval), args.out), indent=2))
        elif args.action == "validate":
            c.bundle(read(args.bundle))
            print("PASS: authoring contracts. Source truth, generation and blind evaluation not verified.")
        elif args.action == "render":
            packet.write_packet(read(args.bundle), args.out)
            print(f"Review packet: {Path(args.out) / 'review.html'}")
        elif args.action == "approve":
            packet.approve(read(args.bundle), args.reviewer, args.note, args.out)
            print("Design approval recorded. No dataset generated.")
        else:
            packet.verify_approval(read(args.approval), read(args.bundle))
            print("PASS: approval matches bundle")
    except (c.Invalid, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0
