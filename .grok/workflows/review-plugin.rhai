let meta = #{
    name: "review-plugin",
    description: "Review aiida-eon jobs, workchains, Elja, and registry",
    phases: [
        #{ title: "Review", detail: "one reviewer per surface" },
        #{ title: "Verify", detail: "adversarial check of each finding" },
    ],
};

let findings_schema = #{
    "type": "object", "required": ["findings"],
    "properties": #{
        "findings": #{ "type": "array", "maxItems": 8, "items": #{
            "type": "object", "required": ["file", "issue"],
            "properties": #{
                "file": #{ "type": "string" },
                "issue": #{ "type": "string" },
            },
        }},
    },
};
let verdict_schema = #{
    "type": "object", "required": ["real", "reason", "evidence"],
    "properties": #{
        "real": #{ "type": "boolean" },
        "reason": #{ "type": "string" },
        "evidence": #{ "type": "string" },
    },
};

let root = if args == () { () } else { args.root };
if root == () { pause("verification", "Pass args.root — path to the aiida-eon checkout."); }

phase("Review");
let dimensions = [
    "CalcJob prepare_for_submission and job catalog correctness",
    "WorkChain outline and expose_inputs bugs",
    "parser results.dat and sidecar handling",
    "Elja computer YAML and helpers vs documented campaign",
    "AiiDA 2.x entry points and registry metadata",
];
let jobs = [];
for d in dimensions {
    let p = "Review the aiida-eon plugin at ";
    p += root;
    p += " for ";
    p += d;
    p += ". Use read_file and grep on the actual files. Report at most 8 concrete ";
    p += "findings as {file, issue}. An empty list is valid only after reading the code.";
    jobs.push(#{
        prompt: p,
        label: "review",
        capability_mode: "read-only",
        output_schema: findings_schema,
    });
}
let results = parallel(jobs);

let findings = [];
for r in results {
    if r != () && r.success && r.output.findings != () {
        for f in r.output.findings { findings.push(f); }
    }
}
if findings.len() == 0 { complete(#{ summary: "No findings.", confirmed: [] }); }

phase("Verify");
let vjobs = [];
for f in findings {
    let vp = "Adversarially verify this review finding by reading the shipped code: \"";
    vp += f.issue;
    vp += "\" in ";
    vp += f.file;
    vp += ". Set real=true only with concrete evidence you independently inspected.";
    vjobs.push(#{
        prompt: vp,
        label: "verify",
        capability_mode: "read-only",
        output_schema: verdict_schema,
    });
}
let verdicts = parallel(vjobs);

let confirmed = [];
let i = 0;
for v in verdicts {
    if v != () && v.success && v.output.real == true
        && v.output.evidence != () && v.output.evidence != "" {
        confirmed.push(findings[i]);
    }
    i += 1;
}
complete(#{ summary: confirmed.len().to_string() + " confirmed findings", confirmed: confirmed });
