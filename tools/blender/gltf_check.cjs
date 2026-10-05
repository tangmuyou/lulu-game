'use strict';
// Run the official Khronos validator, retaining every reported warning.
const fs = require('node:fs');
const path = require('node:path');
async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error('Usage: node gltf_check.cjs input.glb output-directory');
  const modulePath = process.env.GLTF_VALIDATOR_MODULE;
  if (!modulePath) throw new Error('GLTF_VALIDATOR_MODULE is not configured');
  const validator = require(modulePath);
  if (validator.version() !== '2.0.0-dev.3.10') throw new Error('Unexpected validator version');
  const bytes = fs.readFileSync(input);
  const options = {
    uri: path.basename(input), format: 'glb', maxIssues: 0, writeTimestamp: false,
    externalResourceFunction: async (uri) => { throw new Error(`External resource is not allowed in this self-contained GLB: ${uri}`); }
  };
  const report = await validator.validateBytes(new Uint8Array(bytes), options);
  fs.mkdirSync(output, {recursive: true});
  fs.writeFileSync(path.join(output, 'gltf_validation.json'), JSON.stringify(report, null, 2));
  if (report.issues.numErrors !== 0) throw new Error(`GLB contains ${report.issues.numErrors} validation errors`);
  const broken = Buffer.from(bytes);
  broken.writeUInt32LE(0, 0); // Deliberately corrupt only the in-memory copy.
  let rejected = false;
  let negativeResult;
  try {
    negativeResult = await validator.validateBytes(new Uint8Array(broken), {...options, uri: 'intentional-corrupt-test.glb'});
    rejected = negativeResult.issues.numErrors > 0;
  } catch (err) {
    rejected = true;
    negativeResult = {expected_rejection: String(err)};
  }
  fs.writeFileSync(path.join(output, 'expected_corrupt_glb.json'), JSON.stringify(negativeResult, null, 2));
  if (!rejected) throw new Error('Validator did not reject intentionally corrupt GLB bytes');
  const summary = {status: 'passed', validator_version: validator.version(), errors: report.issues.numErrors,
    warnings: report.issues.numWarnings, corrupt_glb_rejected: rejected, godot_runtime_tested: false};
  fs.writeFileSync(path.join(output, 'gltf_validation_summary.json'), JSON.stringify(summary, null, 2));
  console.log('KHRONOS_GLTF_VALIDATION_PASSED', JSON.stringify(summary));
}
main().catch((err) => { console.error(err); process.exitCode = 1; });
