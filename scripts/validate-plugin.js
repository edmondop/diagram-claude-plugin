#!/usr/bin/env node

// Claude Code plugin structure validator.
// Validates marketplace.json + plugin.json against the actual schema
// that Claude Code enforces, plus directory structure checks.
//
// Original validator by Jeremy Longshore (MIT, claude-code-plugins).
// Rewritten to match Claude Code's actual validation rules.

const fs = require("fs");
const path = require("path");

const PLUGIN_JSON_ALLOWED_FIELDS = new Set([
  "name",
  "version",
  "description",
  "author",
  "homepage",
  "repository",
  "license",
  "keywords",
  "commands",
  "agents",
  "hooks",
  "mcpServers",
]);

const MARKETPLACE_REQUIRED_FIELDS = ["name", "plugins"];
const MARKETPLACE_PLUGIN_REQUIRED_FIELDS = ["name", "source"];

function red(s) { return `\x1b[31m${s}\x1b[0m`; }
function green(s) { return `\x1b[32m${s}\x1b[0m`; }
function yellow(s) { return `\x1b[33m${s}\x1b[0m`; }
function cyan(s) { return `\x1b[36m${s}\x1b[0m`; }
function bold(s) { return `\x1b[1m${s}\x1b[0m`; }

class PluginValidator {
  constructor(pluginDir) {
    this.dir = path.resolve(pluginDir);
    this.errors = [];
    this.warnings = [];
    this.passes = [];
  }

  pass(msg) { this.passes.push(msg); }
  error(msg) { this.errors.push(msg); }
  warn(msg) { this.warnings.push(msg); }

  readJSON(relPath) {
    const full = path.join(this.dir, relPath);
    if (!fs.existsSync(full)) return null;
    try {
      return JSON.parse(fs.readFileSync(full, "utf-8"));
    } catch {
      this.error(`${relPath} is not valid JSON`);
      return undefined;
    }
  }

  validate() {
    const name = path.basename(this.dir);
    console.log(cyan("\n" + "=".repeat(60)));
    console.log(bold(`Validating plugin: ${name}`));
    console.log(cyan("=".repeat(60)));

    this.checkStructure();
    this.checkMarketplace();
    this.checkPluginJson();
    this.checkSkills();
    this.checkCommands();
    this.printReport();

    return this.errors.length;
  }

  checkStructure() {
    console.log("\n  Checking directory structure...");

    const metaDir = path.join(this.dir, ".claude-plugin");
    if (!fs.existsSync(metaDir) || !fs.statSync(metaDir).isDirectory()) {
      this.error(".claude-plugin must be a directory, not a file");
      return;
    }
    this.pass(".claude-plugin/ is a directory");

    for (const f of ["marketplace.json", "plugin.json"]) {
      if (fs.existsSync(path.join(metaDir, f))) {
        this.pass(`.claude-plugin/${f} exists`);
      } else {
        this.error(`.claude-plugin/${f} missing`);
      }
    }

    const hasComponent = ["commands", "skills", "agents", "hooks"].some(
      (d) => fs.existsSync(path.join(this.dir, d))
    );
    if (hasComponent) {
      this.pass("Has at least one component directory");
    } else {
      this.warn("No component directories found (commands/, skills/, agents/, hooks/)");
    }
  }

  checkMarketplace() {
    console.log("  Checking marketplace.json...");
    const mkt = this.readJSON(".claude-plugin/marketplace.json");
    if (mkt === null) return;
    if (mkt === undefined) return;

    for (const field of MARKETPLACE_REQUIRED_FIELDS) {
      if (mkt[field]) {
        this.pass(`marketplace.json has required field '${field}'`);
      } else {
        this.error(`marketplace.json missing required field '${field}'`);
      }
    }

    if (!Array.isArray(mkt.plugins) || mkt.plugins.length === 0) {
      this.error("marketplace.json 'plugins' must be a non-empty array");
      return;
    }

    for (const plugin of mkt.plugins) {
      for (const field of MARKETPLACE_PLUGIN_REQUIRED_FIELDS) {
        if (!plugin[field]) {
          this.error(`marketplace.json plugin entry missing '${field}'`);
        }
      }
      if (plugin.source && !plugin.source.startsWith("./")) {
        this.warn(`marketplace.json plugin source should start with './' (got '${plugin.source}')`);
      }
    }
    this.pass("marketplace.json plugins array is valid");
  }

  checkPluginJson() {
    console.log("  Checking plugin.json...");
    const pj = this.readJSON(".claude-plugin/plugin.json");
    if (pj === null) return;
    if (pj === undefined) return;

    if (!pj.name) {
      this.error("plugin.json missing required field 'name'");
    } else {
      if (!/^[a-z0-9-]+$/.test(pj.name)) {
        this.error(`plugin.json name must be kebab-case (got '${pj.name}')`);
      } else {
        this.pass("plugin.json name is valid kebab-case");
      }
    }

    if (pj.version && !/^\d+\.\d+\.\d+/.test(pj.version)) {
      this.error(`plugin.json version must be semver (got '${pj.version}')`);
    }

    const unknownFields = Object.keys(pj).filter(
      (k) => !PLUGIN_JSON_ALLOWED_FIELDS.has(k)
    );
    if (unknownFields.length > 0) {
      this.error(
        `plugin.json has unknown fields: ${unknownFields.join(", ")}. ` +
        `Allowed: ${[...PLUGIN_JSON_ALLOWED_FIELDS].join(", ")}`
      );
    } else {
      this.pass("plugin.json has no unknown fields");
    }

    if (pj.commands) {
      if (!Array.isArray(pj.commands)) {
        this.error("plugin.json 'commands' must be an array of directory paths");
      } else {
        for (const cmd of pj.commands) {
          if (!cmd.startsWith("./")) {
            this.warn(`plugin.json commands path should start with './' (got '${cmd}')`);
          }
        }
      }
    }
  }

  checkSkills() {
    console.log("  Checking skills...");
    const skillsDir = path.join(this.dir, "skills");
    if (!fs.existsSync(skillsDir)) return;

    const skills = fs.readdirSync(skillsDir).filter((d) =>
      fs.statSync(path.join(skillsDir, d)).isDirectory()
    );

    for (const skill of skills) {
      const skillMd = path.join(skillsDir, skill, "SKILL.md");
      if (!fs.existsSync(skillMd)) {
        this.error(`skills/${skill}/ missing SKILL.md`);
        continue;
      }

      const content = fs.readFileSync(skillMd, "utf-8");
      const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
      if (!frontmatter) {
        this.error(`skills/${skill}/SKILL.md missing YAML frontmatter`);
        continue;
      }

      const fm = frontmatter[1];
      if (!fm.includes("name:")) {
        this.error(`skills/${skill}/SKILL.md frontmatter missing 'name'`);
      }
      if (!fm.includes("description:")) {
        this.error(`skills/${skill}/SKILL.md frontmatter missing 'description'`);
      }

      this.pass(`skills/${skill}/SKILL.md has valid frontmatter`);
    }
  }

  checkCommands() {
    console.log("  Checking commands...");
    const cmdsDir = path.join(this.dir, "commands");
    if (!fs.existsSync(cmdsDir)) return;

    const cmds = fs.readdirSync(cmdsDir).filter((f) => f.endsWith(".md"));
    for (const cmd of cmds) {
      const content = fs.readFileSync(path.join(cmdsDir, cmd), "utf-8");
      const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
      if (!frontmatter) {
        this.warn(`commands/${cmd} missing YAML frontmatter`);
        continue;
      }
      this.pass(`commands/${cmd} has valid frontmatter`);
    }
  }

  printReport() {
    console.log(cyan("\n" + "=".repeat(60)));
    console.log(bold("Report"));
    console.log(cyan("=".repeat(60)));

    if (this.passes.length > 0) {
      console.log(green(`\n  PASSED (${this.passes.length})`));
      for (const p of this.passes) console.log(green(`    ${p}`));
    }

    if (this.warnings.length > 0) {
      console.log(yellow(`\n  WARNINGS (${this.warnings.length})`));
      for (const w of this.warnings) console.log(yellow(`    ${w}`));
    }

    if (this.errors.length > 0) {
      console.log(red(`\n  ERRORS (${this.errors.length})`));
      for (const e of this.errors) console.log(red(`    ${e}`));
    }

    console.log(cyan("\n" + "=".repeat(60)));
    if (this.errors.length === 0) {
      console.log(green("  PASS — plugin structure is valid\n"));
    } else {
      console.log(red(`  FAIL — ${this.errors.length} error(s) found\n`));
    }
  }
}

const pluginDir = process.argv[2];
if (!pluginDir) {
  console.error("Usage: validate-plugin.js <plugin-directory>");
  process.exit(1);
}
if (!fs.existsSync(pluginDir)) {
  console.error(`Directory not found: ${pluginDir}`);
  process.exit(1);
}

const validator = new PluginValidator(pluginDir);
const errorCount = validator.validate();
process.exit(errorCount > 0 ? 1 : 0);
