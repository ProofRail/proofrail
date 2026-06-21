# Silver Verifier Output Attestation — Example Files

These examples are illustrative only. They are not cryptographically verifiable without runtime keys.

The example attestation shape shows the JSON structure produced by `tools/silver/sign_verifier_output_attestation_v0_1_0.py`. Placeholder hashes and signatures are used.

To produce a real, verifiable attestation, run the Make targets:

```bash
make silver-demo-001
make generate-silver-verifier-attestor-demo-001
make sign-silver-verifier-attestation-demo-001
make verify-silver-verifier-attestation-demo-001
```

Or run the full regression test:

```bash
make verify-silver-attestation-v0-2-2
```
