// Usage: node extract.mjs REPO_DIR > graph.json
// Emits {nodes:[{id,kind,name,file,start,end,exported}], edges:[{type,src,dst}]} for the working tree.
import { Project, SyntaxKind, Node } from "ts-morph";
import path from "node:path";
import fs from "node:fs";

const root = path.resolve(process.argv[2]).replaceAll("\\", "/");
const project = new Project({ tsConfigFilePath: path.join(root, "tsconfig.json"), skipFileDependencyResolution: false });
const rel = (p) => path.relative(root, p).replaceAll("\\", "/");
const inRepo = (sf) => sf && !sf.isInNodeModules() && !sf.isDeclarationFile() && sf.getFilePath().replaceAll("\\", "/").startsWith(root + "/");
const isTest = (f) => /\.(test|spec)(-d)?\.[cm]?[tj]sx?$/.test(f);

const nodes = new Map(), edges = new Set(), declId = new Map();
const addNode = (n) => nodes.set(n.id, n);
const addEdge = (type, src, dst) => src && dst && src !== dst && edges.add(JSON.stringify([type, src, dst]));
const fileId = (f) => `file:${f}`;

// Declarations that become function/class nodes
function declName(d) {
  if ((Node.isFunctionDeclaration(d) || Node.isMethodDeclaration(d) || Node.isConstructorDeclaration(d)) && !d.getBody()) return; // skip overload signatures / ambient
  if (Node.isFunctionDeclaration(d) || Node.isClassDeclaration(d) || Node.isInterfaceDeclaration(d) || Node.isTypeAliasDeclaration(d) || Node.isEnumDeclaration(d)) return d.getName();
  if (Node.isMethodDeclaration(d) || Node.isConstructorDeclaration(d) || Node.isGetAccessorDeclaration(d) || Node.isSetAccessorDeclaration(d)) {
    const c = d.getParent(); const cn = Node.isClassDeclaration(c) || Node.isClassExpression(c) ? (c.getName() ?? "<anon>") : "<obj>";
    return `${cn}.${Node.isConstructorDeclaration(d) ? "constructor" : d.getName()}`;
  }
  if (Node.isVariableDeclaration(d)) {
    const i = d.getInitializer();
    if (i && (Node.isArrowFunction(i) || Node.isFunctionExpression(i))) return d.getName();
  }
}
const kindOf = (d) => Node.isClassDeclaration(d) ? "class" : (Node.isInterfaceDeclaration(d) || Node.isTypeAliasDeclaration(d) || Node.isEnumDeclaration(d)) ? "type" : "function";

const files = project.getSourceFiles().filter(inRepo);
const fileSet = new Set(files.map((sf) => rel(sf.getFilePath())));

// Workspace-package resolution: package.json name -> in-repo dir. ts-morph resolves
// cross-package specs via node_modules (dist/.d.ts) or not at all -> module: edges.
const pkgRoots = {};
(function scanPkgs(dir, depth) {
  if (depth > 3) return;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === "node_modules" || e.name.startsWith(".")) continue;
    const p = dir + "/" + e.name;
    if (e.isDirectory()) scanPkgs(p, depth + 1);
    else if (e.name === "package.json" && depth > 0) {
      try { const nm = JSON.parse(fs.readFileSync(p, "utf8")).name; if (nm) pkgRoots[nm] = rel(p).split("/").slice(0, -1).join("/"); } catch {}
    }
  }
})(root, 0);

const tryFile = (stem) => [stem, stem + ".ts", stem + ".tsx", stem + ".mts", stem + ".cts", stem + ".js", stem + ".jsx", stem + "/index.ts", stem + "/index.tsx", stem + "/index.js"].find((c) => fileSet.has(c));
function wsResolve(spec) {
  if (spec.startsWith(".") || spec.startsWith("node:")) return null;
  const parts = spec.split("/");
  const n = spec.startsWith("@") ? 2 : 1;
  const name = parts.slice(0, n).join("/"), sub = parts.slice(n).join("/");
  const dir = pkgRoots[name];
  if (!dir) return null;
  const cands = [];
  if (sub) for (const b of [dir, dir + "/src"]) cands.push(`${b}/${sub}`);
  else {
    try {
      const pj = JSON.parse(fs.readFileSync(root + "/" + dir + "/package.json", "utf8"));
      const src = pj.source ?? pj.exports?.["."]?.source;
      if (typeof src === "string") cands.push(dir + "/" + src.replace(/^\.\//, ""));
    } catch {}
    cands.push(dir + "/src/index", dir + "/index");
  }
  for (const stem of cands) { const hit = tryFile(stem); if (hit) return hit; }
  return null;
}

for (const sf of files) {
  const f = rel(sf.getFilePath());
  addNode({ id: fileId(f), kind: isTest(f) ? "test_file" : "file", name: f, file: f, start: 1, end: sf.getEndLineNumber(), exported: false });
  const decls = [...sf.getDescendants().filter((d) => declName(d) !== undefined)];
  for (const d of decls) {
    const name = declName(d);
    let id = `${kindOf(d)}:${f}#${name}`;
    if (nodes.has(id)) id += `@${d.getStartLineNumber()}`;
    const exported = Node.isExportable(d) ? d.isExported() : Node.isVariableDeclaration(d) ? d.getVariableStatement()?.isExported() ?? false : false;
    addNode({ id, kind: kindOf(d), name, file: f, start: d.getStartLineNumber(), end: d.getEndLineNumber(), exported });
    declId.set(d, id);
    addEdge("defined_in", id, fileId(f));
  }
}

const idOfDecl = (d) => { for (let n = d; n; n = n.getParent()) if (declId.has(n)) return declId.get(n); };
const resolveDecls = (node) => {
  let s = node.getSymbol();
  if (s?.isAlias()) s = s.getAliasedSymbol() ?? s;
  return (s?.getDeclarations() ?? []).filter((d) => inRepo(d.getSourceFile()));
};
const enclosingAny = (n, f) => { for (let p = n.getParent(); p; p = p.getParent()) if (declId.has(p)) return declId.get(p); return fileId(f); };
const enclosing = (n, f) => { for (let p = n.getParent(); p; p = p.getParent()) if (declId.has(p) && kindOf(p) === "function") return declId.get(p); return fileId(f); };

for (const sf of files) {
  const f = rel(sf.getFilePath());
  const fid = fileId(f);
  // imports / re-exports
  for (const d of [...sf.getImportDeclarations(), ...sf.getExportDeclarations()]) {
    const spec = d.getModuleSpecifierValue?.();
    if (!spec) continue;
    const target = d.getModuleSpecifierSourceFile?.();
    const ws = inRepo(target) ? null : wsResolve(spec);
    if (inRepo(target)) addEdge("imports", fid, fileId(rel(target.getFilePath())));
    else if (ws) addEdge("imports", fid, fileId(ws));
    else if (!spec.startsWith(".")) { const m = spec.startsWith("node:") ? spec : spec.split("/").slice(0, spec.startsWith("@") ? 2 : 1).join("/"); addNode({ id: `module:${m}`, kind: "module", name: m, file: "", start: 0, end: 0, exported: false }); addEdge("imports", fid, `module:${m}`); }
  }
  // calls + new
  for (const c of [...sf.getDescendantsOfKind(SyntaxKind.CallExpression), ...sf.getDescendantsOfKind(SyntaxKind.NewExpression)]) {
    const e = c.getExpression();
    const src = enclosing(c, f);
    for (const d of resolveDecls(e)) {
      const t = idOfDecl(d);
      if (!t) continue;
      addEdge("calls", src, t);
    }
  }
  // extends / implements
  for (const c of sf.getDescendantsOfKind(SyntaxKind.ClassDeclaration)) {
    const id = declId.get(c);
    const ex = c.getExtends()?.getExpression();
    if (ex) for (const d of resolveDecls(ex)) addEdge("extends", id, idOfDecl(d));
    for (const i of c.getImplements()) for (const d of resolveDecls(i.getExpression())) addEdge("implements", id, idOfDecl(d));
  }
  for (const i of sf.getDescendantsOfKind(SyntaxKind.InterfaceDeclaration)) for (const e of i.getExtends()) for (const d of resolveDecls(e.getExpression())) addEdge("extends", declId.get(i), idOfDecl(d));
  // uses_type
  for (const r of sf.getDescendantsOfKind(SyntaxKind.TypeReference)) {
    const src = enclosingAny(r, f);
    for (const d of resolveDecls(r.getTypeName())) { const t = idOfDecl(d); if (t && nodes.get(t)?.kind !== "function") addEdge("uses_type", src, t); }
  }
}
process.stdout.write(JSON.stringify({ commit: process.argv[3] ?? null, nodes: [...nodes.values()], edges: [...edges].map((e) => { const [type, src, dst] = JSON.parse(e); return { type, src, dst }; }) }));
